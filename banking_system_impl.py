from banking_system import BankingSystem
import heapq

MILLISECONDS_IN_1_DAY = 86400000

class BankingSystemImpl(BankingSystem):

    def __init__(self):
        self.accounts = {}

        # Level 3 - payment records with a min-heap of due_time, payment_id
        # makes earliest cashback due is at index 0
        self.payments = {}
        self.pending_cashbacks = []

    def _process_cashbacks(self, timestamp: int) -> None:
        """
        Refunds all of the pending cashback when due time is ready for the refund. 
        Methods that read or changes a balance or payment status needs to call
        this first so that cashback occurs before anything else at the given timestamp.
        """
        # earliest due time at index 0, stops at the first one that's not due yet
        while self.pending_cashbacks and self.pending_cashbacks[0][0] <= timestamp:
            _, payment_id = heapq.heappop(self.pending_cashbacks) 
            payment = self.payments[payment_id] 
            self.accounts[payment["account_id"]]["balance"] += payment["cashback"]
            payment["status"] = "CASHBACK_RECEIVED"

    def create_account(self, timestamp: int, account_id: str) -> bool:
        if account_id in self.accounts:
            return False

        self.accounts[account_id] = {
            "account_opened" : timestamp, 
            "balance": 0,
            "total_outgoing":0 
        }

        return True 

    def deposit(self, timestamp: int, account_id: str, amount: int) -> int | None:
        self._process_cashbacks(timestamp)

        if account_id in self.accounts:
            self.accounts[account_id]["balance"] += amount 
            return self.accounts[account_id]["balance"]
        
        return None

    def transfer(self, timestamp: int, source_account_id: str, target_account_id: str, amount: int) -> int | None:
        self._process_cashbacks(timestamp)

        if (source_account_id != target_account_id
            and source_account_id in self.accounts 
            and target_account_id in self.accounts 
            and self.accounts[source_account_id]["balance"] >= amount): 
              
              self.accounts[source_account_id]["balance"] -= amount
              self.accounts[target_account_id]["balance"] += amount

              #Track total outgoing transactions for source account
              self.accounts[source_account_id]["total_outgoing"] += amount

              return self.accounts[source_account_id]["balance"]
        
        return None

    def top_spenders(self, timestamp: int, n: int) -> list[str]:
        sorted_accounts=sorted(self.accounts.items(), key=lambda x: (-x[1]["total_outgoing"], x[0])
                               )
        
        return [
            f"{account_id}({account_data['total_outgoing']})"
            for account_id, account_data in sorted_accounts[:n]
        ]

    def pay(self, timestamp: int, account_id: str, amount: int) -> str | None:
        self._process_cashbacks(timestamp)

        if account_id not in self.accounts or self.accounts[account_id]["balance"] < amount:
            
            return None

        # withdraw and count it as outgoing which allows top_spenders to see it 
        self.accounts[account_id]["balance"] -= amount 
        self.accounts[account_id]["total_outgoing"] += amount

        # payment ids are numbered across all accounts. payments are never deleted
        # so the count is then going to be the next number 
        payment_id = f"payment{len(self.payments) + 1}"
        self.payments[payment_id] = { 
            "account_id": account_id,
            "cashback": amount * 2 // 100,
            "status": "IN_PROGRESS" 
        }

        # schedules the 2% refund 24 hours after
        heapq.heappush(self.pending_cashbacks, (timestamp + MILLISECONDS_IN_1_DAY, payment_id))

        return payment_id

    def get_payment_status(self, timestamp: int, account_id: str, payment: str) -> str | None:
        self._process_cashbacks(timestamp)

        if account_id not in self.accounts or payment not in self.payments: 
            return None

        # payment exists but belongs to a different account
        if self.payments[payment]["account_id"] != account_id: 
            return None

        return self.payments[payment]["status"] 

    
