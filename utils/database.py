"""Supabase database client for crypto trading app."""
from supabase import create_client, Client
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from config import Config


class SupabaseDB:
    """Database manager for Supabase operations."""
    
    def __init__(self):
        """Initialize Supabase client."""
        if not Config.is_configured():
            raise ValueError("Supabase configuration is missing. Please set up .env file.")
        
        self.client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    # ==================== USER OPERATIONS ====================
    
    def get_user_by_google_id(self, google_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Google ID."""
        try:
            response = self.client.table('Users').select('*').eq('google_id', google_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        try:
            response = self.client.table('Users').select('*').eq('email', email).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    def create_user(self, google_id: str, email: str, name: str) -> Optional[Dict[str, Any]]:
        """Create a new user and initialize their wallets."""
        try:
            # Create user
            user_data = {
                'google_id': google_id,
                'email': email,
                'name': name,
                'created_at': datetime.now().isoformat()
            }
            
            response = self.client.table('Users').insert(user_data).execute()
            user = response.data[0] if response.data else None
            
            if user:
                # Initialize wallets with default currencies
                self.initialize_user_wallets(user['user_id'])
            
            return user
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user information."""
        try:
            self.client.table('Users').update(kwargs).eq('user_id', user_id).execute()
            return True
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
    
    # ==================== WALLET OPERATIONS ====================
    
    def initialize_user_wallets(self, user_id: int):
        """Initialize wallets for a new user with default currencies."""
        try:
            # First, check if user already has wallets
            existing = self.client.table('Wallets').select('*').eq('user_id', user_id).execute()
            
            if existing.data:
                # User has old wallets - delete them and recreate with new currencies
                self.client.table('Wallets').delete().eq('user_id', user_id).execute()
                print(f"Cleaned up old wallets for user {user_id}")
            
            wallets = []
            for currency in Config.DEFAULT_CURRENCIES:
                # USDT gets initial balance, others start at 0
                balance = Config.INITIAL_BALANCE if currency == 'USDT' else 0.0
                
                wallets.append({
                    'user_id': user_id,
                    'currency': currency,
                    'balance': balance,
                    'locked_balance': 0.0
                })
            
            self.client.table('Wallets').insert(wallets).execute()
            print(f"Initialized {len(wallets)} wallets for user {user_id}")
            return True
        except Exception as e:
            print(f"Error initializing wallets: {e}")
            return False
    
    def get_user_wallets(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all wallets for a user."""
        try:
            response = self.client.table('Wallets').select('*').eq('user_id', user_id).execute()
            return response.data or []
        except Exception as e:
            print(f"Error getting wallets: {e}")
            return []
    
    def get_wallet_balance(self, user_id: int, currency: str) -> Optional[Dict[str, Any]]:
        """Get balance for a specific currency."""
        try:
            response = self.client.table('Wallets').select('*').eq('user_id', user_id).eq('currency', currency).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting wallet balance: {e}")
            return None
    
    def update_wallet_balance(self, user_id: int, currency: str, balance: float, locked_balance: float = None) -> bool:
        """Update wallet balance."""
        try:
            update_data = {'balance': balance}
            if locked_balance is not None:
                update_data['locked_balance'] = locked_balance
            
            self.client.table('Wallets').update(update_data).eq('user_id', user_id).eq('currency', currency).execute()
            return True
        except Exception as e:
            print(f"Error updating wallet balance: {e}")
            return False
    
    # ==================== ORDER OPERATIONS ====================
    
    def create_order(self, user_id: int, pair: str, order_type: str, side: str, 
                    price: float, amount: float, status: str = 'pending') -> Optional[Dict[str, Any]]:
        """Create a new order."""
        try:
            order_data = {
                'user_id': user_id,
                'pair': pair,
                'type': order_type,
                'side': side,
                'price': price,
                'amount': amount,
                'status': status,
                'timestamp': datetime.now().isoformat()
            }
            
            response = self.client.table('Orders').insert(order_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating order: {e}")
            return None
    
    def get_user_orders(self, user_id: int, status: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get orders for a user, optionally filtered by status."""
        try:
            query = self.client.table('Orders').select('*').eq('user_id', user_id)
            
            if status:
                query = query.eq('status', status)
            
            response = query.order('timestamp', desc=True).limit(limit).execute()
            return response.data or []
        except Exception as e:
            print(f"Error getting orders: {e}")
            return []
    
    def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific order by ID."""
        try:
            response = self.client.table('Orders').select('*').eq('order_id', order_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting order: {e}")
            return None
    
    def update_order_status(self, order_id: int, status: str) -> bool:
        """Update order status."""
        try:
            self.client.table('Orders').update({'status': status}).eq('order_id', order_id).execute()
            return True
        except Exception as e:
            print(f"Error updating order status: {e}")
            return False
    
    def cancel_order(self, order_id: int) -> bool:
        """Cancel an order."""
        return self.update_order_status(order_id, 'cancelled')
    
    # ==================== TRANSACTION OPERATIONS ====================
    
    def create_transaction(self, user_id: int, order_id: int, pair: str, 
                          transaction_type: str, amount: float, price: float, 
                          fee: float = 0.0) -> Optional[Dict[str, Any]]:
        """Create a new transaction."""
        try:
            transaction_data = {
                'user_id': user_id,
                'order_id': order_id,
                'pair': pair,
                'type': transaction_type,
                'amount': amount,
                'price': price,
                'fee': fee,
                'timestamp': datetime.now().isoformat()
            }
            
            response = self.client.table('Transactions').insert(transaction_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error creating transaction: {e}")
            return None
    
    def get_user_transactions(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Get transaction history for a user."""
        try:
            response = (self.client.table('Transactions')
                       .select('*')
                       .eq('user_id', user_id)
                       .order('timestamp', desc=True)
                       .limit(limit)
                       .execute())
            return response.data or []
        except Exception as e:
            print(f"Error getting transactions: {e}")
            return []
    
    def get_transactions_by_pair(self, user_id: int, pair: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get transactions for a specific trading pair."""
        try:
            response = (self.client.table('Transactions')
                       .select('*')
                       .eq('user_id', user_id)
                       .eq('pair', pair)
                       .order('timestamp', desc=True)
                       .limit(limit)
                       .execute())
            return response.data or []
        except Exception as e:
            print(f"Error getting transactions by pair: {e}")
            return []
    
    # ==================== TRADING OPERATIONS ====================
    
    def execute_market_order(self, user_id: int, pair: str, side: str, 
                            amount: float, current_price: float) -> Dict[str, Any]:
        """
        Execute a market order (buy/sell at current market price).
        
        Args:
            user_id: User ID
            pair: Trading pair (e.g., 'BTC/USDT')
            side: 'buy' or 'sell'
            amount: Amount to trade
            current_price: Current market price
        
        Returns:
            Dict with success status and details
        """
        try:
            # Parse trading pair
            base_currency, quote_currency = pair.split('/')
            
            # Calculate total cost (including 0.1% fee)
            fee_rate = 0.001
            total_cost = amount * current_price
            fee = total_cost * fee_rate
            
            # Get user wallets
            if side == 'buy':
                # Check if user has enough quote currency (e.g., USDT)
                quote_wallet = self.get_wallet_balance(user_id, quote_currency)
                if not quote_wallet or quote_wallet['balance'] < (total_cost + fee):
                    return {'success': False, 'error': 'Insufficient balance'}
                
                # Update wallets
                new_quote_balance = quote_wallet['balance'] - total_cost - fee
                self.update_wallet_balance(user_id, quote_currency, new_quote_balance)
                
                base_wallet = self.get_wallet_balance(user_id, base_currency)
                new_base_balance = (base_wallet['balance'] if base_wallet else 0.0) + amount
                self.update_wallet_balance(user_id, base_currency, new_base_balance)
                
            else:  # sell
                # Check if user has enough base currency (e.g., BTC)
                base_wallet = self.get_wallet_balance(user_id, base_currency)
                if not base_wallet or base_wallet['balance'] < amount:
                    return {'success': False, 'error': 'Insufficient balance'}
                
                # Update wallets
                new_base_balance = base_wallet['balance'] - amount
                self.update_wallet_balance(user_id, base_currency, new_base_balance)
                
                quote_wallet = self.get_wallet_balance(user_id, quote_currency)
                new_quote_balance = (quote_wallet['balance'] if quote_wallet else 0.0) + total_cost - fee
                self.update_wallet_balance(user_id, quote_currency, new_quote_balance)
            
            # Create order record
            order = self.create_order(
                user_id=user_id,
                pair=pair,
                order_type='market',
                side=side,
                price=current_price,
                amount=amount,
                status='filled'
            )
            
            # Create transaction record
            if order:
                transaction = self.create_transaction(
                    user_id=user_id,
                    order_id=order['order_id'],
                    pair=pair,
                    transaction_type=side,
                    amount=amount,
                    price=current_price,
                    fee=fee
                )
            
            return {
                'success': True,
                'order': order,
                'transaction': transaction,
                'fee': fee
            }
            
        except Exception as e:
            print(f"Error executing market order: {e}")
            return {'success': False, 'error': str(e)}
    
    # ==================== UTILITY OPERATIONS ====================
    
    def get_portfolio_value(self, user_id: int, prices: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculate total portfolio value in USDT.
        
        Args:
            user_id: User ID
            prices: Dict of current prices {currency: price_in_usdt}
        
        Returns:
            Dict with total value and breakdown by currency
        """
        try:
            wallets = self.get_user_wallets(user_id)
            total_value = 0.0
            breakdown = []
            
            for wallet in wallets:
                currency = wallet['currency']
                balance = wallet['balance']
                
                # USDT is already in USDT, others need conversion
                if currency == 'USDT':
                    value_in_usdt = balance
                else:
                    price = prices.get(currency, 0.0)
                    value_in_usdt = balance * price
                
                total_value += value_in_usdt
                breakdown.append({
                    'currency': currency,
                    'balance': balance,
                    'value_usdt': value_in_usdt
                })
            
            return {
                'total_value': total_value,
                'breakdown': breakdown
            }
        except Exception as e:
            print(f"Error calculating portfolio value: {e}")
            return {'total_value': 0.0, 'breakdown': []}
    
    # ==================== DAILY LOGIN BONUS ====================
    
    def claim_daily_bonus(self, user_id: int) -> Dict[str, Any]:
        """
        Claim daily login bonus for user.
        Bonus: $50 USDT per day (resets at midnight UTC)
        
        Returns:
            Dict with success status, bonus amount, and next claim time
        """
        try:
            # Get user's last login
            user = self.client.table('Users').select('last_login_bonus').eq('user_id', user_id).execute()
            if not user.data:
                return {'success': False, 'message': 'User not found'}
            
            last_bonus = user.data[0].get('last_login_bonus')
            now = datetime.now(timezone.utc)  # Use UTC timezone
            
            # Check if user can claim (must be 24 hours since last claim)
            if last_bonus:
                # Parse the timestamp from database (it's already timezone-aware)
                if isinstance(last_bonus, str):
                    last_bonus_time = datetime.fromisoformat(last_bonus.replace('Z', '+00:00'))
                else:
                    last_bonus_time = last_bonus
                
                hours_since = (now - last_bonus_time).total_seconds() / 3600
                
                if hours_since < 24:
                    hours_remaining = 24 - hours_since
                    return {
                        'success': False,
                        'message': f'Bonus already claimed. Next bonus in {hours_remaining:.1f} hours',
                        'hours_remaining': hours_remaining
                    }
            
            # Give bonus - $50 USDT
            bonus_amount = 50.0
            
            # Update USDT wallet
            usdt_wallet = self.get_wallet_balance(user_id, 'USDT')
            print(f"[DEBUG] Daily Bonus - Current USDT wallet: {usdt_wallet}")
            
            if usdt_wallet:
                old_balance = usdt_wallet['balance']
                new_balance = old_balance + bonus_amount
                print(f"[DEBUG] Daily Bonus - Old balance: ${old_balance}, Adding: ${bonus_amount}, New balance: ${new_balance}")
                
                success = self.update_wallet_balance(user_id, 'USDT', new_balance)
                print(f"[DEBUG] Daily Bonus - Wallet update success: {success}")
                
                if not success:
                    return {'success': False, 'message': 'Failed to update wallet balance'}
                
                # Update last bonus time
                self.client.table('Users').update({
                    'last_login_bonus': now.isoformat()
                }).eq('user_id', user_id).execute()
                
                print(f"[DEBUG] Daily Bonus - Completed! User {user_id} received ${bonus_amount}")
                
                return {
                    'success': True,
                    'bonus_amount': bonus_amount,
                    'new_balance': new_balance,
                    'message': f'Daily bonus claimed! +${bonus_amount} USDT'
                }
            
            return {'success': False, 'message': 'USDT wallet not found'}
            
        except Exception as e:
            print(f"Error claiming daily bonus: {e}")
            return {'success': False, 'message': str(e)}
    
    # ==================== LEADERBOARD & RANKING ====================
    
    def get_leaderboard(self, prices: Dict[str, float], limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get leaderboard of richest users by total portfolio value.
        
        Args:
            prices: Current crypto prices
            limit: Maximum number of users to return
        
        Returns:
            List of users ranked by total assets
        """
        try:
            # Get all users
            users = self.client.table('Users').select('user_id, name, email').execute()
            
            leaderboard = []
            for user in users.data:
                user_id = user['user_id']
                portfolio = self.get_portfolio_value(user_id, prices)
                
                leaderboard.append({
                    'rank': 0,  # Will be set later
                    'user_id': user_id,
                    'name': user['name'],
                    'email': user['email'],
                    'total_value': portfolio['total_value'],
                    'breakdown': portfolio['breakdown']
                })
            
            # Sort by total value descending
            leaderboard.sort(key=lambda x: x['total_value'], reverse=True)
            
            # Assign ranks
            for i, entry in enumerate(leaderboard[:limit]):
                entry['rank'] = i + 1
            
            return leaderboard[:limit]
            
        except Exception as e:
            print(f"Error getting leaderboard: {e}")
            return []
    
    def get_coin_leaderboard(self, currency: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get leaderboard for a specific cryptocurrency.
        
        Args:
            currency: Crypto symbol (BTC, ETH, etc.)
            limit: Maximum number of users
        
        Returns:
            List of users ranked by holdings of specific coin
        """
        try:
            # Get all wallets for this currency
            wallets = self.client.table('Wallets').select('user_id, balance').eq('currency', currency).execute()
            
            # Get user details
            leaderboard = []
            for wallet in wallets.data:
                user_id = wallet['user_id']
                user = self.client.table('Users').select('name, email').eq('user_id', user_id).execute()
                
                if user.data:
                    leaderboard.append({
                        'rank': 0,
                        'user_id': user_id,
                        'name': user.data[0]['name'],
                        'email': user.data[0]['email'],
                        'balance': wallet['balance'],
                        'currency': currency
                    })
            
            # Sort by balance descending
            leaderboard.sort(key=lambda x: x['balance'], reverse=True)
            
            # Assign ranks
            for i, entry in enumerate(leaderboard[:limit]):
                entry['rank'] = i + 1
            
            return leaderboard[:limit]
            
        except Exception as e:
            print(f"Error getting coin leaderboard: {e}")
            return []
    
    def get_user_rank(self, user_id: int, prices: Dict[str, float]) -> Dict[str, Any]:
        """
        Get user's rank among all users.
        
        Returns:
            Dict with rank, total users, and percentile
        """
        try:
            leaderboard = self.get_leaderboard(prices, limit=10000)
            
            total_users = len(leaderboard)
            user_rank = None
            user_value = 0.0
            
            for entry in leaderboard:
                if entry['user_id'] == user_id:
                    user_rank = entry['rank']
                    user_value = entry['total_value']
                    break
            
            if user_rank:
                percentile = ((total_users - user_rank) / total_users) * 100
                return {
                    'rank': user_rank,
                    'total_users': total_users,
                    'percentile': percentile,
                    'total_value': user_value
                }
            
            return {'rank': None, 'total_users': total_users}
            
        except Exception as e:
            print(f"Error getting user rank: {e}")
            return {'rank': None, 'total_users': 0}
    
    # ==================== P2P TRADING METHODS ====================
    
    def create_trade_offer(self, user_id: str, offering_currency: str, offering_amount: float,
                          requesting_currency: str, requesting_amount: float) -> dict:
        """Create a new P2P trade offer."""
        try:
            # Check if user has sufficient balance
            wallet = self.get_wallet_balance(user_id, offering_currency)
            if not wallet:
                return {'success': False, 'error': f'You do not have a {offering_currency} wallet'}
            
            balance = Decimal(str(wallet['balance']))
            offering_decimal = Decimal(str(offering_amount))
            
            if balance < offering_decimal:
                return {
                    'success': False,
                    'error': f'Insufficient {offering_currency} balance. Available: {balance}'
                }
            
            # Lock the funds by reducing available balance
            new_balance = balance - offering_decimal
            locked_balance = Decimal(str(wallet['locked_balance'])) + offering_decimal
            
            self.client.table('Wallets').update({
                'balance': str(new_balance),
                'locked_balance': str(locked_balance)
            }).eq('user_id', user_id).eq('currency', offering_currency).execute()
            
            # Create the offer
            offer_data = {
                'creator_id': user_id,
                'offering_currency': offering_currency,
                'offering_amount': str(offering_amount),
                'requesting_currency': requesting_currency,
                'requesting_amount': str(requesting_amount),
                'status': 'active'
            }
            
            result = self.client.table('TradeOffers').insert(offer_data).execute()
            
            return {'success': True, 'offer': result.data[0] if result.data else None}
            
        except Exception as e:
            print(f"Error creating trade offer: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def get_all_trade_offers(self, exclude_user_id: str = None) -> list:
        """Get all active trade offers, optionally excluding a specific user's offers."""
        try:
            query = self.client.table('TradeOffers').select(
                '*, Users!TradeOffers_creator_id_fkey(name)'
            ).eq('status', 'active').order('created_at', desc=True)
            
            result = query.execute()
            
            offers = []
            for offer in result.data:
                # Skip offers from the excluded user
                if exclude_user_id and offer['creator_id'] == exclude_user_id:
                    continue
                
                # Extract creator name from joined data
                creator_name = offer.get('Users', {}).get('name', 'Unknown') if isinstance(offer.get('Users'), dict) else 'Unknown'
                
                offer_dict = {
                    'offer_id': offer['offer_id'],
                    'creator_id': offer['creator_id'],
                    'creator_name': creator_name,
                    'offering_currency': offer['offering_currency'],
                    'offering_amount': offer['offering_amount'],
                    'requesting_currency': offer['requesting_currency'],
                    'requesting_amount': offer['requesting_amount'],
                    'created_at': offer['created_at']
                }
                offers.append(offer_dict)
            
            return offers
            
        except Exception as e:
            print(f"Error getting trade offers: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_user_trade_offers(self, user_id: str) -> list:
        """Get all active offers created by a specific user."""
        try:
            result = self.client.table('TradeOffers').select('*').eq(
                'creator_id', user_id
            ).eq('status', 'active').order('created_at', desc=True).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting user trade offers: {e}")
            return []
    
    def accept_trade_offer(self, acceptor_id: str, offer_id: str) -> dict:
        """Accept a P2P trade offer and execute the trade."""
        try:
            # Get the offer
            offer_result = self.client.table('TradeOffers').select('*').eq(
                'offer_id', offer_id
            ).eq('status', 'active').execute()
            
            if not offer_result.data:
                return {'success': False, 'error': 'Offer not found or already completed'}
            
            offer = offer_result.data[0]
            creator_id = offer['creator_id']
            
            # Can't accept your own offer
            if acceptor_id == creator_id:
                return {'success': False, 'error': 'You cannot accept your own offer'}
            
            offering_currency = offer['offering_currency']
            offering_amount = Decimal(str(offer['offering_amount']))
            requesting_currency = offer['requesting_currency']
            requesting_amount = Decimal(str(offer['requesting_amount']))
            
            # Check if acceptor has sufficient balance
            acceptor_wallet = self.get_wallet_balance(acceptor_id, requesting_currency)
            if not acceptor_wallet:
                return {'success': False, 'error': f'You do not have a {requesting_currency} wallet'}
            
            acceptor_balance = Decimal(str(acceptor_wallet['balance']))
            if acceptor_balance < requesting_amount:
                return {
                    'success': False,
                    'error': f'Insufficient {requesting_currency} balance. Need: {requesting_amount}, Have: {acceptor_balance}'
                }
            
            # Execute the trade
            # 1. Transfer offering_currency from creator's locked balance to acceptor
            creator_offer_wallet = self.get_wallet_balance(creator_id, offering_currency)
            creator_locked = Decimal(str(creator_offer_wallet['locked_balance']))
            
            # Unlock creator's funds (already deducted from balance when offer was created)
            new_creator_locked = creator_locked - offering_amount
            
            self.client.table('Wallets').update({
                'locked_balance': str(new_creator_locked)
            }).eq('user_id', creator_id).eq('currency', offering_currency).execute()
            
            # Give offering_currency to acceptor
            acceptor_offer_wallet = self.get_wallet_balance(acceptor_id, offering_currency)
            if acceptor_offer_wallet:
                acceptor_offer_balance = Decimal(str(acceptor_offer_wallet['balance']))
                self.client.table('Wallets').update({
                    'balance': str(acceptor_offer_balance + offering_amount)
                }).eq('user_id', acceptor_id).eq('currency', offering_currency).execute()
            
            # 2. Transfer requesting_currency from acceptor to creator
            # Deduct from acceptor
            self.client.table('Wallets').update({
                'balance': str(acceptor_balance - requesting_amount)
            }).eq('user_id', acceptor_id).eq('currency', requesting_currency).execute()
            
            # Give to creator
            creator_request_wallet = self.get_wallet_balance(creator_id, requesting_currency)
            if creator_request_wallet:
                creator_request_balance = Decimal(str(creator_request_wallet['balance']))
                self.client.table('Wallets').update({
                    'balance': str(creator_request_balance + requesting_amount)
                }).eq('user_id', creator_id).eq('currency', requesting_currency).execute()
            
            # 3. Mark offer as completed
            self.client.table('TradeOffers').update({
                'status': 'completed',
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('offer_id', offer_id).execute()
            
            # 4. Record the transaction
            transaction_data = {
                'offer_id': offer_id,
                'creator_id': creator_id,
                'acceptor_id': acceptor_id,
                'offering_currency': offering_currency,
                'offering_amount': str(offering_amount),
                'requesting_currency': requesting_currency,
                'requesting_amount': str(requesting_amount)
            }
            
            self.client.table('P2PTradeTransactions').insert(transaction_data).execute()
            
            return {
                'success': True,
                'received_currency': offering_currency,
                'received_amount': float(offering_amount),
                'sent_currency': requesting_currency,
                'sent_amount': float(requesting_amount)
            }
            
        except Exception as e:
            print(f"Error accepting trade offer: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def cancel_trade_offer(self, offer_id: str, user_id: str) -> dict:
        """Cancel a P2P trade offer and unlock funds."""
        try:
            # Get the offer
            offer_result = self.client.table('TradeOffers').select('*').eq(
                'offer_id', offer_id
            ).eq('creator_id', user_id).eq('status', 'active').execute()
            
            if not offer_result.data:
                return {'success': False, 'error': 'Offer not found or you are not the creator'}
            
            offer = offer_result.data[0]
            offering_currency = offer['offering_currency']
            offering_amount = Decimal(str(offer['offering_amount']))
            
            # Unlock the funds
            wallet = self.get_wallet_balance(user_id, offering_currency)
            if wallet:
                balance = Decimal(str(wallet['balance']))
                locked = Decimal(str(wallet['locked_balance']))
                
                new_balance = balance + offering_amount
                new_locked = locked - offering_amount
                
                self.client.table('Wallets').update({
                    'balance': str(new_balance),
                    'locked_balance': str(new_locked)
                }).eq('user_id', user_id).eq('currency', offering_currency).execute()
            
            # Mark offer as cancelled
            self.client.table('TradeOffers').update({
                'status': 'cancelled',
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('offer_id', offer_id).execute()
            
            return {'success': True}
            
        except Exception as e:
            print(f"Error cancelling trade offer: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

