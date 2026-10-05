--!strict
-- Coins. A balance is a whole number from 0 up to MAX; an amount moved is a whole number of at least 1.
local Wallet = {}

Wallet.MAX = 10 ^ 15 -- far below where whole numbers stop being exact

function Wallet.isAmount(n: any): boolean
	return type(n) == "number" and n == n and n % 1 == 0 and n >= 1 and n <= Wallet.MAX
end

-- A stored balance, or `fallback` when what was stored is not a valid one.
function Wallet.sanitize(raw: any, fallback: number): number
	if type(raw) == "number" and raw == raw and raw % 1 == 0 and raw >= 0 and raw <= Wallet.MAX then
		return raw
	end
	return fallback
end

-- The balance after receiving n, or nil if n is not a valid amount or the balance would pass MAX.
function Wallet.add(balance: number, n: any): number?
	if not Wallet.isAmount(n) or balance + n > Wallet.MAX then
		return nil
	end
	return balance + n
end

-- The balance after paying n, or nil if n is not a valid amount or there is not enough.
function Wallet.spend(balance: number, n: any): number?
	if not Wallet.isAmount(n) or n > balance then
		return nil
	end
	return balance - n
end

return Wallet
