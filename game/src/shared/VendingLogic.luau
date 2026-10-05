--!strict
-- A vending machine: one kind of thing, one price, and a stock held inside the machine.
-- In "sell" mode visitors buy from the stock and the coins go to the owner. In "buy" mode visitors
-- sell into the stock and the coins come from the owner, until the stock reaches the owner's limit.
-- Every function either does the whole job or changes nothing, and nothing is created or lost:
-- items only move between a bag and the stock, coins only between the two balances.
local VendingLogic = {}

export type Bag = { [string]: number }
export type State = {
	item: string?,
	price: number,
	mode: string, -- "sell" or "buy"
	stock: number,
	limit: number, -- in buy mode, buying stops when the stock reaches this
}

VendingLogic.MAX_PRICE = 10 ^ 9
VendingLogic.MAX_STOCK = 100000
VendingLogic.DEFAULT_LIMIT = 64
local LIMIT = 2 ^ 31 -- a bag never holds this many of one thing
local MAX_COINS = 10 ^ 15

local function isWhole(n: any, low: number, high: number): boolean
	return type(n) == "number" and n == n and n % 1 == 0 and n >= low and n <= high
end

local function take(bag: Bag, key: string, n: number)
	local left = (bag[key] or 0) - n
	if left > 0 then
		bag[key] = left
	else
		bag[key] = nil
	end
end

function VendingLogic.new(): State
	return { item = nil, price = 0, mode = "sell", stock = 0, limit = VendingLogic.DEFAULT_LIMIT }
end

function VendingLogic.isReady(state: State): boolean
	return state.item ~= nil and state.price >= 1
end

-- The owner sets what the machine deals in. Choosing a different thing first puts the old stock
-- back in the owner's bag.
function VendingLogic.configure(
	state: State,
	ownerBag: Bag,
	item: any,
	price: any,
	mode: any,
	limit: any,
	isKey: (any) -> boolean
): (boolean, string?)
	if type(item) ~= "string" or not isKey(item) then
		return false, "item"
	end
	if not isWhole(price, 1, VendingLogic.MAX_PRICE) then
		return false, "price"
	end
	if mode ~= "sell" and mode ~= "buy" then
		return false, "mode"
	end
	if not isWhole(limit, 1, VendingLogic.MAX_STOCK) then
		return false, "limit"
	end
	local old = state.item
	if old and old ~= item and state.stock > 0 then
		if (ownerBag[old] or 0) + state.stock >= LIMIT then
			return false, "full"
		end
		ownerBag[old] = (ownerBag[old] or 0) + state.stock
		state.stock = 0
	end
	state.item, state.price, state.mode, state.limit = item, price, mode, limit
	return true, nil
end

-- The owner moves n from their bag into the machine.
function VendingLogic.deposit(state: State, ownerBag: Bag, n: any): (boolean, string?)
	local item = state.item
	if not item then
		return false, "unset"
	end
	if not isWhole(n, 1, VendingLogic.MAX_STOCK) then
		return false, "amount"
	end
	if (ownerBag[item] or 0) < n then
		return false, "missing"
	end
	if state.stock + n > VendingLogic.MAX_STOCK then
		return false, "full"
	end
	take(ownerBag, item, n)
	state.stock += n
	return true, nil
end

-- The owner moves n from the machine back into their bag.
function VendingLogic.withdraw(state: State, ownerBag: Bag, n: any): (boolean, string?)
	local item = state.item
	if not item then
		return false, "unset"
	end
	if not isWhole(n, 1, VendingLogic.MAX_STOCK) then
		return false, "amount"
	end
	if state.stock < n then
		return false, "missing"
	end
	if (ownerBag[item] or 0) + n >= LIMIT then
		return false, "full"
	end
	state.stock -= n
	ownerBag[item] = (ownerBag[item] or 0) + n
	return true, nil
end

-- A visitor buys n from a machine that sells. Returns the visitor's and the owner's new balances.
function VendingLogic.purchase(
	state: State,
	visitorBag: Bag,
	visitorCoins: number,
	ownerCoins: number,
	n: any
): (boolean, string?, number, number)
	local item = state.item
	if not item or state.mode ~= "sell" or not VendingLogic.isReady(state) then
		return false, "closed", visitorCoins, ownerCoins
	end
	if not isWhole(n, 1, VendingLogic.MAX_STOCK) then
		return false, "amount", visitorCoins, ownerCoins
	end
	if state.stock < n then
		return false, "stock", visitorCoins, ownerCoins
	end
	local cost = state.price * n
	if cost > visitorCoins then
		return false, "coins", visitorCoins, ownerCoins
	end
	if ownerCoins + cost > MAX_COINS or (visitorBag[item] or 0) + n >= LIMIT then
		return false, "full", visitorCoins, ownerCoins
	end
	state.stock -= n
	visitorBag[item] = (visitorBag[item] or 0) + n
	return true, nil, visitorCoins - cost, ownerCoins + cost
end

-- How many more a buying machine will take: up to its limit, and what the owner can pay for.
function VendingLogic.wanted(state: State, ownerCoins: number): number
	if state.mode ~= "buy" or not VendingLogic.isReady(state) then
		return 0
	end
	local room = math.min(state.limit, VendingLogic.MAX_STOCK) - state.stock
	return math.max(0, math.min(room, math.floor(ownerCoins / state.price)))
end

-- A visitor sells n to a machine that buys. Returns the visitor's and the owner's new balances.
function VendingLogic.supply(
	state: State,
	visitorBag: Bag,
	visitorCoins: number,
	ownerCoins: number,
	n: any
): (boolean, string?, number, number)
	local item = state.item
	if not item or state.mode ~= "buy" or not VendingLogic.isReady(state) then
		return false, "closed", visitorCoins, ownerCoins
	end
	if not isWhole(n, 1, VendingLogic.MAX_STOCK) then
		return false, "amount", visitorCoins, ownerCoins
	end
	if (visitorBag[item] or 0) < n then
		return false, "missing", visitorCoins, ownerCoins
	end
	if state.stock + n > math.min(state.limit, VendingLogic.MAX_STOCK) then
		return false, "limit", visitorCoins, ownerCoins
	end
	local cost = state.price * n
	if cost > ownerCoins then
		return false, "ownercoins", visitorCoins, ownerCoins
	end
	if visitorCoins + cost > MAX_COINS then
		return false, "full", visitorCoins, ownerCoins
	end
	take(visitorBag, item, n)
	state.stock += n
	return true, nil, visitorCoins + cost, ownerCoins - cost
end

-- Rebuilds a state from stored data, dropping anything that is not valid.
function VendingLogic.sanitize(raw: any, isKey: (any) -> boolean): State
	local state = VendingLogic.new()
	if type(raw) ~= "table" then
		return state
	end
	if type(raw.item) == "string" and isKey(raw.item) then
		state.item = raw.item
		if isWhole(raw.price, 1, VendingLogic.MAX_PRICE) then
			state.price = raw.price
		end
		if isWhole(raw.stock, 0, VendingLogic.MAX_STOCK) then
			state.stock = raw.stock
		end
	end
	if raw.mode == "buy" then
		state.mode = "buy"
	end
	if isWhole(raw.limit, 1, VendingLogic.MAX_STOCK) then
		state.limit = raw.limit
	end
	return state
end

return VendingLogic
