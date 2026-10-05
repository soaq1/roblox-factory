--!strict
-- Buying from and selling to a merchant. A merchant has a list of prices; the player's bag and
-- coins change together or not at all.
local ShopLogic = {}

export type Bag = { [string]: number }
export type PriceList = { [string]: number }

ShopLogic.MAX_AT_ONCE = 9999 -- most of one thing in a single purchase or sale
local LIMIT = 2 ^ 31 -- a bag never holds this many of one thing
local MAX_COINS = 10 ^ 15

local function isCount(n: any): boolean
	return type(n) == "number" and n == n and n % 1 == 0 and n >= 1 and n <= ShopLogic.MAX_AT_ONCE
end

local function priceOf(prices: PriceList?, key: any): number?
	if type(prices) ~= "table" or type(key) ~= "string" then
		return nil
	end
	local price = prices[key]
	if type(price) == "number" and price == price and price % 1 == 0 and price >= 1 then
		return price
	end
	return nil
end

-- Pays coins for n of something the merchant sells. Returns the new balance.
function ShopLogic.buy(
	bag: Bag,
	coins: number,
	prices: PriceList?,
	key: any,
	n: any
): (boolean, string?, number)
	local price = priceOf(prices, key)
	if not price then
		return false, "unknown", coins
	end
	if not isCount(n) then
		return false, "amount", coins
	end
	local cost = price * n
	if cost > coins then
		return false, "coins", coins
	end
	if (bag[key] or 0) + n >= LIMIT then
		return false, "full", coins
	end
	bag[key] = (bag[key] or 0) + n
	return true, nil, coins - cost
end

-- Hands over n of something the merchant buys. Returns the new balance.
function ShopLogic.sell(
	bag: Bag,
	coins: number,
	prices: PriceList?,
	key: any,
	n: any
): (boolean, string?, number)
	local price = priceOf(prices, key)
	if not price then
		return false, "unknown", coins
	end
	if not isCount(n) then
		return false, "amount", coins
	end
	local have = bag[key] or 0
	if have < n then
		return false, "missing", coins
	end
	local gain = price * n
	if coins + gain > MAX_COINS then
		return false, "full", coins
	end
	if have == n then
		bag[key] = nil
	else
		bag[key] = have - n
	end
	return true, nil, coins + gain
end

-- How many of something the coins can pay for, up to the most allowed at once.
function ShopLogic.affordable(coins: number, prices: PriceList?, key: any): number
	local price = priceOf(prices, key)
	if not price then
		return 0
	end
	return math.clamp(math.floor(coins / price), 0, ShopLogic.MAX_AT_ONCE)
end

return ShopLogic
