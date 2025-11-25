"""Neon PostgreSQL database adapter."""
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Optional, List, Dict, Any
from config import Config


class NeonDB:
    """Direct PostgreSQL connection for Neon database."""
    
    def __init__(self):
        """Initialize Neon PostgreSQL connection."""
        self.conn = psycopg2.connect(Config.NEON_DATABASE_URL, cursor_factory=RealDictCursor)
        self.conn.autocommit = True
    
    def _execute(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a query and return results."""
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params or ())
                try:
                    return cur.fetchall()
                except:
                    return []
        except Exception as e:
            print(f"Database query error: {e}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            import traceback
            traceback.print_exc()
            return []
    
    def _execute_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Execute a query and return one result."""
        results = self._execute(query, params)
        return dict(results[0]) if results else None
    
    # User operations
    def get_user_by_google_id(self, google_id: str) -> Optional[Dict]:
        """Get user by Google ID."""
        query = 'SELECT * FROM "Users" WHERE google_id = %s'
        return self._execute_one(query, (google_id,))
    
    def create_user(self, google_id: str, email: str, name: str) -> Optional[Dict]:
        """Create a new user."""
        query = '''
            INSERT INTO "Users" (google_id, email, name, created_at)
            VALUES (%s, %s, %s, %s)
            RETURNING *
        '''
        user = self._execute_one(query, (google_id, email, name, datetime.now()))
        if user:
            self.initialize_user_wallets(user['user_id'])
        return user
    
    def initialize_user_wallets(self, user_id: int):
        """Initialize wallets for a user."""
        # Delete existing wallets
        self._execute('DELETE FROM "Wallets" WHERE user_id = %s', (user_id,))
        
        # Insert new wallets
        for currency in Config.DEFAULT_CURRENCIES:
            balance = Config.INITIAL_BALANCE if currency == 'USDT' else 0.0
            query = '''
                INSERT INTO "Wallets" (user_id, currency, balance, locked_balance)
                VALUES (%s, %s, %s, 0.0)
            '''
            self._execute(query, (user_id, currency, balance))
    
    def get_user_wallets(self, user_id: int) -> List[Dict]:
        """Get all wallets for a user."""
        query = 'SELECT * FROM "Wallets" WHERE user_id = %s ORDER BY currency'
        return self._execute(query, (user_id,))
    
    def get_all_wallets(self, user_id: int) -> List[Dict]:
        """Get all wallets for a user (alias for get_user_wallets)."""
        return self.get_user_wallets(user_id)
    
    def get_wallet_balance(self, user_id: int, currency: str) -> Optional[Dict]:
        """Get wallet balance for specific currency."""
        query = 'SELECT * FROM "Wallets" WHERE user_id = %s AND currency = %s'
        return self._execute_one(query, (user_id, currency))
    
    def execute_market_order(self, user_id: int, pair: str, side: str, amount: float, current_price: float) -> Dict:
        """Execute a market order."""
        try:
            from decimal import Decimal
            
            base, quote = pair.split('/')
            total = float(amount) * float(current_price)
            fee = total * 0.001  # 0.1% fee
            total_cost = total + fee
            
            print(f"[TRADE] Executing {side} order: {amount} {base} @ ${current_price}")
            print(f"[TRADE] Amount: {amount}, Price: {current_price}, Total: ${total:.2f}, Fee: ${fee:.2f}")
            print(f"[TRADE] Total cost with fee: ${total_cost:.2f}")
            
            if side == 'buy':
                # Check USDT balance
                wallet = self.get_wallet_balance(user_id, quote)
                current_balance = float(wallet['balance']) if wallet else 0
                print(f"[TRADE] Current {quote} balance: ${current_balance:.2f}")
                
                if not wallet or current_balance < total_cost:
                    return {'success': False, 'error': f'Insufficient {quote} balance'}
                
                # Deduct USDT - EXPLICIT float conversion
                deduct_amount = float(total_cost)
                print(f"[TRADE] Deducting ${deduct_amount:.2f} {quote}...")
                print(f"[TRADE] SQL: UPDATE Wallets SET balance = balance - {deduct_amount} WHERE user_id = {user_id} AND currency = '{quote}'")
                
                self._execute(
                    'UPDATE "Wallets" SET balance = balance - %s WHERE user_id = %s AND currency = %s',
                    (deduct_amount, user_id, quote)
                )
                
                # Verify deduction
                wallet_after = self.get_wallet_balance(user_id, quote)
                new_balance = float(wallet_after['balance']) if wallet_after else 0
                actual_deducted = current_balance - new_balance
                print(f"[TRADE] New {quote} balance: ${new_balance:.2f}")
                print(f"[TRADE] Actually deducted: ${actual_deducted:.2f} (expected: ${deduct_amount:.2f})")
                
                if abs(actual_deducted - deduct_amount) > 0.01:
                    print(f"[TRADE] ⚠️ WARNING: Deduction mismatch! Expected -{deduct_amount:.2f} but got -{actual_deducted:.2f}")
                
                # Add base currency
                add_amount = float(amount)
                print(f"[TRADE] Adding {add_amount} {base}...")
                self._execute(
                    'UPDATE "Wallets" SET balance = balance + %s WHERE user_id = %s AND currency = %s',
                    (add_amount, user_id, base)
                )
                
                # Verify addition
                base_wallet = self.get_wallet_balance(user_id, base)
                print(f"[TRADE] New {base} balance: {base_wallet['balance'] if base_wallet else 'NULL'}")
                
            else:  # sell
                # Check base currency balance
                wallet = self.get_wallet_balance(user_id, base)
                if not wallet or wallet['balance'] < amount:
                    return {'success': False, 'error': f'Insufficient {base} balance'}
                
                # Deduct base currency
                self._execute(
                    'UPDATE "Wallets" SET balance = balance - %s WHERE user_id = %s AND currency = %s',
                    (amount, user_id, base)
                )
                
                # Add USDT (minus fee)
                self._execute(
                    'UPDATE "Wallets" SET balance = balance + %s WHERE user_id = %s AND currency = %s',
                    (total - fee, user_id, quote)
                )
            
            # Record transaction
            print(f"[TRADE] Recording transaction in database...")
            self._execute('''
                INSERT INTO "Transactions" (user_id, pair, type, amount, price, fee, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (user_id, pair, side, amount, current_price, fee, datetime.now()))
            
            print(f"[TRADE] ✅ Trade executed successfully!")
            return {'success': True, 'fee': fee}
            
        except Exception as e:
            print(f"[TRADE] ❌ Error executing order: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_recent_transactions(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get recent transactions."""
        query = '''
            SELECT * FROM "Transactions" 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s
        '''
        return self._execute(query, (user_id, limit))
    
    def get_user_transactions(self, user_id: int, limit: int = 100) -> List[Dict]:
        """Get transaction history for a user."""
        query = '''
            SELECT * FROM "Transactions" 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s
        '''
        return self._execute(query, (user_id, limit))
    
    def get_portfolio_value(self, user_id: int, prices: Dict) -> Dict:
        """Calculate total portfolio value."""
        wallets = self.get_user_wallets(user_id)
        total = 0.0
        breakdown = []
        
        for wallet in wallets:
            currency = wallet['currency']
            balance = float(wallet['balance'])
            
            if currency == 'USDT':
                value = balance
            else:
                pair = f"{currency}/USDT"
                price = prices.get(pair, 0)
                value = balance * price
            
            total += value
            if balance > 0:
                breakdown.append({
                    'currency': currency,
                    'balance': balance,
                    'value': value
                })
        
        return {
            'total_value': total,
            'breakdown': breakdown
        }
    
    # Leaderboard operations
    def get_leaderboard(self, prices: Dict, limit: int = 100) -> List[Dict]:
        """Get leaderboard of users ranked by total portfolio value."""
        try:
            users = self._execute('SELECT user_id, name, email FROM "Users"')
            leaderboard = []
            
            for user in users:
                portfolio = self.get_portfolio_value(user['user_id'], prices)
                leaderboard.append({
                    'rank': 0,
                    'user_id': user['user_id'],
                    'name': user['name'],
                    'email': user['email'],
                    'total_value': portfolio['total_value'],
                    'breakdown': portfolio['breakdown']
                })
            
            # Sort by total value
            leaderboard.sort(key=lambda x: x['total_value'], reverse=True)
            
            # Assign ranks
            for i, entry in enumerate(leaderboard[:limit]):
                entry['rank'] = i + 1
            
            return leaderboard[:limit]
        except Exception as e:
            print(f"Error getting leaderboard: {e}")
            return []
    
    def get_coin_leaderboard(self, currency: str, limit: int = 100) -> List[Dict]:
        """Get leaderboard for a specific cryptocurrency."""
        try:
            query = '''
                SELECT w.user_id, w.balance, u.name, u.email
                FROM "Wallets" w
                JOIN "Users" u ON w.user_id = u.user_id
                WHERE w.currency = %s
                ORDER BY w.balance DESC
                LIMIT %s
            '''
            results = self._execute(query, (currency, limit))
            
            leaderboard = []
            for i, row in enumerate(results):
                leaderboard.append({
                    'rank': i + 1,
                    'user_id': row['user_id'],
                    'name': row['name'],
                    'email': row['email'],
                    'balance': float(row['balance']),
                    'currency': currency
                })
            
            return leaderboard
        except Exception as e:
            print(f"Error getting coin leaderboard: {e}")
            return []
    
    def get_user_rank(self, user_id: int, prices: Dict) -> Dict:
        """Get user's rank among all users."""
        try:
            leaderboard = self.get_leaderboard(prices, limit=10000)
            total_users = len(leaderboard)
            
            for entry in leaderboard:
                if entry['user_id'] == user_id:
                    percentile = ((total_users - entry['rank']) / total_users) * 100
                    return {
                        'rank': entry['rank'],
                        'total_users': total_users,
                        'percentile': percentile,
                        'total_value': entry['total_value']
                    }
            
            return {'rank': None, 'total_users': total_users}
        except Exception as e:
            print(f"Error getting user rank: {e}")
            return {'rank': None, 'total_users': 0}
    
    # P2P Trading operations
    def create_trade_offer(self, user_id: int, offering_currency: str, offering_amount: float,
                          requesting_currency: str, requesting_amount: float) -> Dict:
        """Create a new P2P trade offer."""
        try:
            # Check balance
            wallet = self.get_wallet_balance(user_id, offering_currency)
            if not wallet or wallet['balance'] < offering_amount:
                return {'success': False, 'error': f'Insufficient {offering_currency} balance'}
            
            # Lock funds
            self._execute('''
                UPDATE "Wallets" 
                SET balance = balance - %s, locked_balance = locked_balance + %s
                WHERE user_id = %s AND currency = %s
            ''', (offering_amount, offering_amount, user_id, offering_currency))
            
            # Create offer
            result = self._execute('''
                INSERT INTO "TradeOffers" 
                (creator_id, offering_currency, offering_amount, requesting_currency, requesting_amount, status, created_at)
                VALUES (%s, %s, %s, %s, %s, 'active', %s)
                RETURNING *
            ''', (user_id, offering_currency, offering_amount, requesting_currency, requesting_amount, datetime.now()))
            
            return {'success': True, 'offer': dict(result[0]) if result else None}
        except Exception as e:
            print(f"Error creating trade offer: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_all_trade_offers(self, exclude_user_id: int = None) -> List[Dict]:
        """Get all active trade offers."""
        try:
            query = '''
                SELECT t.*, u.name as creator_name
                FROM "TradeOffers" t
                JOIN "Users" u ON t.creator_id = u.user_id
                WHERE t.status = 'active'
            '''
            params = ()
            
            if exclude_user_id:
                query += ' AND t.creator_id != %s'
                params = (exclude_user_id,)
            
            query += ' ORDER BY t.created_at DESC'
            
            results = self._execute(query, params if params else None)
            return [dict(r) for r in results]
        except Exception as e:
            print(f"Error getting trade offers: {e}")
            return []
    
    def get_user_trade_offers(self, user_id: int) -> List[Dict]:
        """Get user's active trade offers."""
        query = '''
            SELECT * FROM "TradeOffers"
            WHERE creator_id = %s AND status = 'active'
            ORDER BY created_at DESC
        '''
        results = self._execute(query, (user_id,))
        return [dict(r) for r in results]
    
    def accept_trade_offer(self, acceptor_id: int, offer_id: int) -> Dict:
        """Accept a P2P trade offer."""
        try:
            # Get offer
            offer = self._execute_one('SELECT * FROM "TradeOffers" WHERE offer_id = %s AND status = %s', 
                                     (offer_id, 'active'))
            if not offer:
                return {'success': False, 'error': 'Offer not found'}
            
            if acceptor_id == offer['creator_id']:
                return {'success': False, 'error': 'Cannot accept your own offer'}
            
            # Check acceptor balance
            acceptor_wallet = self.get_wallet_balance(acceptor_id, offer['requesting_currency'])
            if not acceptor_wallet or acceptor_wallet['balance'] < float(offer['requesting_amount']):
                return {'success': False, 'error': f'Insufficient {offer["requesting_currency"]} balance'}
            
            # Execute trade
            # Deduct from acceptor
            self._execute('''
                UPDATE "Wallets" SET balance = balance - %s
                WHERE user_id = %s AND currency = %s
            ''', (offer['requesting_amount'], acceptor_id, offer['requesting_currency']))
            
            # Add to acceptor
            self._execute('''
                UPDATE "Wallets" SET balance = balance + %s
                WHERE user_id = %s AND currency = %s
            ''', (offer['offering_amount'], acceptor_id, offer['offering_currency']))
            
            # Unlock and deduct from creator
            self._execute('''
                UPDATE "Wallets" SET locked_balance = locked_balance - %s
                WHERE user_id = %s AND currency = %s
            ''', (offer['offering_amount'], offer['creator_id'], offer['offering_currency']))
            
            # Add to creator
            self._execute('''
                UPDATE "Wallets" SET balance = balance + %s
                WHERE user_id = %s AND currency = %s
            ''', (offer['requesting_amount'], offer['creator_id'], offer['requesting_currency']))
            
            # Mark offer as completed
            self._execute('UPDATE "TradeOffers" SET status = %s WHERE offer_id = %s', ('completed', offer_id))
            
            # Record transaction
            self._execute('''
                INSERT INTO "P2PTradeTransactions" (offer_id, acceptor_id, status, created_at)
                VALUES (%s, %s, 'completed', %s)
            ''', (offer_id, acceptor_id, datetime.now()))
            
            return {
                'success': True,
                'received_currency': offer['offering_currency'],
                'received_amount': float(offer['offering_amount']),
                'sent_currency': offer['requesting_currency'],
                'sent_amount': float(offer['requesting_amount'])
            }
        except Exception as e:
            print(f"Error accepting trade offer: {e}")
            return {'success': False, 'error': str(e)}
    
    def cancel_trade_offer(self, offer_id: int, user_id: int) -> Dict:
        """Cancel a trade offer and unlock funds."""
        try:
            # Get offer
            offer = self._execute_one('''
                SELECT * FROM "TradeOffers" 
                WHERE offer_id = %s AND creator_id = %s AND status = 'active'
            ''', (offer_id, user_id))
            
            if not offer:
                return {'success': False, 'error': 'Offer not found'}
            
            # Unlock funds
            self._execute('''
                UPDATE "Wallets"
                SET balance = balance + %s, locked_balance = locked_balance - %s
                WHERE user_id = %s AND currency = %s
            ''', (offer['offering_amount'], offer['offering_amount'], user_id, offer['offering_currency']))
            
            # Mark as cancelled
            self._execute('UPDATE "TradeOffers" SET status = %s WHERE offer_id = %s', ('cancelled', offer_id))
            
            return {'success': True}
        except Exception as e:
            print(f"Error cancelling trade offer: {e}")
            return {'success': False, 'error': str(e)}
    
    def claim_daily_bonus(self, user_id: int) -> Dict:
        """Claim daily login bonus with 24-hour cooldown."""
        try:
            from datetime import datetime, timedelta
            
            # Check last bonus time from Users table
            user = self._execute_one('SELECT last_login_bonus FROM "Users" WHERE user_id = %s', (user_id,))
            
            now = datetime.now()
            today = now.date()
            
            # First check: Users.last_login_bonus
            if user and user.get('last_login_bonus'):
                last_bonus = user['last_login_bonus']
                if isinstance(last_bonus, str):
                    from dateutil import parser
                    last_bonus = parser.parse(last_bonus)
                
                # Calculate hours since last bonus
                hours_since = (now - last_bonus).total_seconds() / 3600
                if hours_since < 24:
                    return {
                        'success': False,
                        'message': f'Bonus already claimed. Next bonus in {24 - hours_since:.1f} hours',
                        'hours_remaining': 24 - hours_since
                    }
            
            # Second check: DailyLogins table (backup verification)
            last_claim = self._execute_one('''
                SELECT login_date, bonus_amount 
                FROM "DailyLogins" 
                WHERE user_id = %s 
                ORDER BY login_date DESC 
                LIMIT 1
            ''', (user_id,))
            
            if last_claim:
                last_claim_date = last_claim['login_date']
                if isinstance(last_claim_date, str):
                    from dateutil import parser
                    last_claim_date = parser.parse(last_claim_date).date()
                
                # Prevent claiming twice on the same day
                if last_claim_date >= today:
                    # Calculate time until midnight
                    tomorrow = today + timedelta(days=1)
                    midnight = datetime.combine(tomorrow, datetime.min.time())
                    hours_remaining = (midnight - now).total_seconds() / 3600
                    
                    return {
                        'success': False,
                        'message': f'Bonus already claimed today. Next bonus in {hours_remaining:.1f} hours',
                        'hours_remaining': hours_remaining
                    }
            
            # Give $50 USDT bonus
            bonus = 50.0
            
            # Update wallet
            self._execute('''
                UPDATE "Wallets" SET balance = balance + %s
                WHERE user_id = %s AND currency = 'USDT'
            ''', (bonus, user_id))
            
            # Update last bonus time in Users table
            self._execute('UPDATE "Users" SET last_login_bonus = %s WHERE user_id = %s', 
                         (now, user_id))
            
            # Record in DailyLogins table
            self._execute('''
                INSERT INTO "DailyLogins" (user_id, login_date, bonus_amount)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, login_date) DO NOTHING
            ''', (user_id, today, bonus))
            
            wallet = self.get_wallet_balance(user_id, 'USDT')
            return {
                'success': True,
                'bonus_amount': bonus,
                'new_balance': wallet['balance'] if wallet else bonus,
                'message': f'Daily bonus claimed! +${bonus} USDT'
            }
        except Exception as e:
            print(f"Error claiming daily bonus: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': str(e)}
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

