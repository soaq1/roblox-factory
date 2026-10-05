-- Merchants and vending machines:  lune run tests/shop_test.luau
local T = require("./harness")
local Defs = require("../src/shared/Defs")
local Prices = require("../src/shared/Prices")
local Recipes = require("../src/shared/Recipes")
local ShopLogic = require("../src/shared/ShopLogic")
local VendingLogic = require("../src/shared/VendingLogic")
local Stock = (require("../src/shared/Stock") :: any)(Defs)

local test, eq = T.test, T.eq
local MERCHANTS = { farmer = true, miner = true, cook = true, builder = true }
local BAD_AMOUNTS: { any } = { 0, -1, 1.5, 0 / 0, math.huge, "3", 1e12 }

-- The price list
test("every price is a whole positive number for a real thing at a real merchant", function()
	for _, side in { Prices.sells, Prices.buys } do
		for merchant, list in side do
			assert(MERCHANTS[merchant], "unknown merchant " .. merchant)
			for key, price in list do
				assert(Stock.isKey(key), merchant .. " deals in unknown " .. key)
				assert(type(price) == "number" and price % 1 == 0 and price >= 1, key .. " has a bad price")
			end
		end
	end
end)
test("the game sells only seeds, saplings and decoration blocks", function()
	local used = {}
	for _, recipe in Recipes.craft do
		for key in recipe.ins do
			used[key] = true
		end
	end
	for _, cost in Recipes.upgrades do
		for key in cost do
			used[key] = true
		end
	end
	for _, list in Recipes.byMachine do
		for _, recipe in list do
			for key in recipe.ins do
				used[key] = true
			end
		end
	end
	for merchant, list in Prices.sells do
		for key in list do
			assert(not Defs.isMachine(key), merchant .. " sells a machine: " .. key)
			assert(not used[key], merchant .. " sells a recipe ingredient: " .. key)
			local block = Stock.blockOf(key)
			if block then
				-- a block that breaks into an item would turn coins into that item
				eq(Stock.blockDrop(block, 0.5), key, key .. " breaks into")
			else
				assert(key == "seed" or key == "sapling", merchant .. " sells " .. key)
			end
		end
	end
end)
test("nothing is bought back for as much as it is sold for", function()
	for _, selling in Prices.sells do
		for key, price in selling do
			for merchant, buying in Prices.buys do
				assert(not buying[key] or buying[key] < price, merchant .. " buys " .. key .. " at a profit")
			end
		end
	end
end)

-- Merchants
test("buying takes coins and gives the goods", function()
	local bag = { seed = 2 }
	local ok, _, coins = ShopLogic.buy(bag, 100, Prices.sells.farmer, "seed", 5)
	eq(ok, true)
	eq(bag.seed, 7)
	eq(coins, 100 - 5 * Prices.sells.farmer.seed)
end)
test("buying fails whole without enough coins", function()
	local bag = {}
	local ok, reason, coins = ShopLogic.buy(bag, 49, Prices.sells.farmer, "sapling", 1)
	eq(ok, false)
	eq(reason, "coins")
	eq(coins, 49)
	eq(next(bag), nil)
end)
test("selling takes the goods and gives coins", function()
	local bag = { wheat = 10 }
	local ok, _, coins = ShopLogic.sell(bag, 5, Prices.buys.farmer, "wheat", 10)
	eq(ok, true)
	eq(bag.wheat, nil)
	eq(coins, 5 + 10 * Prices.buys.farmer.wheat)
end)
test("nobody sells what they do not hold", function()
	local bag = { wheat = 3 }
	local ok, reason, coins = ShopLogic.sell(bag, 0, Prices.buys.farmer, "wheat", 4)
	eq(ok, false)
	eq(reason, "missing")
	eq(coins, 0)
	eq(bag.wheat, 3)
end)
test("a merchant only deals in what is on their list", function()
	local bag = { ingot_fe = 5, smelter = 1 }
	local _, reason = ShopLogic.sell(bag, 0, Prices.buys.farmer, "ingot_fe", 1)
	eq(reason, "unknown")
	_, reason = ShopLogic.buy(bag, 1e9, Prices.sells.farmer, "smelter", 1)
	eq(reason, "unknown")
	_, reason = ShopLogic.buy(bag, 1e9, nil, "seed", 1)
	eq(reason, "unknown")
	_, reason = ShopLogic.buy(bag, 1e9, Prices.sells.farmer, 7, 1)
	eq(reason, "unknown")
	eq(bag.ingot_fe, 5)
	eq(bag.smelter, 1)
end)
test("merchants refuse odd amounts", function()
	for _, n in BAD_AMOUNTS do
		local bag = { wheat = 50 }
		local ok, reason, coins = ShopLogic.sell(bag, 7, Prices.buys.farmer, "wheat", n)
		eq(ok, false)
		eq(reason, "amount")
		eq(coins, 7)
		eq(bag.wheat, 50)
		ok, reason, coins = ShopLogic.buy(bag, 1e9, Prices.sells.farmer, "seed", n)
		eq(ok, false)
		eq(reason, "amount")
		eq(coins, 1e9)
		eq(bag.seed, nil)
	end
end)
test("what the coins can pay for is counted right", function()
	eq(ShopLogic.affordable(105, Prices.sells.farmer, "seed"), 10)
	eq(ShopLogic.affordable(9, Prices.sells.farmer, "seed"), 0)
	eq(ShopLogic.affordable(1e12, Prices.sells.farmer, "seed"), ShopLogic.MAX_AT_ONCE)
	eq(ShopLogic.affordable(100, Prices.sells.farmer, "banana"), 0)
end)

-- Vending machines
local function selling(item: string, price: number, stock: number)
	local state = VendingLogic.new()
	local bag = { [item] = stock }
	assert(VendingLogic.configure(state, bag, item, price, "sell", 64, Stock.isKey), "could not set up")
	assert(stock == 0 or VendingLogic.deposit(state, bag, stock), "could not stock")
	return state
end
local function buying(item: string, price: number, limit: number)
	local state = VendingLogic.new()
	assert(VendingLogic.configure(state, {}, item, price, "buy", limit, Stock.isKey), "could not set up")
	return state
end
test("an owner stocks a machine from the bag and takes it back", function()
	local state = VendingLogic.new()
	local bag = { ingot_fe = 30 }
	eq(VendingLogic.deposit(state, bag, 5), false)
	eq(VendingLogic.configure(state, bag, "ingot_fe", 20, "sell", 64, Stock.isKey), true)
	eq(VendingLogic.deposit(state, bag, 25), true)
	eq(bag.ingot_fe, 5)
	eq(state.stock, 25)
	local ok, reason = VendingLogic.deposit(state, bag, 6)
	eq(ok, false)
	eq(reason, "missing")
	eq(VendingLogic.withdraw(state, bag, 10), true)
	eq(bag.ingot_fe, 15)
	eq(state.stock, 15)
	ok, reason = VendingLogic.withdraw(state, bag, 16)
	eq(reason, "missing")
	eq(state.stock, 15)
end)
test("a machine can deal in machines and blocks as well as items", function()
	for _, key in { "smelter", "block:planks", "core_fe" } do
		eq(VendingLogic.configure(VendingLogic.new(), {}, key, 1, "sell", 1, Stock.isKey), true)
	end
end)
test("a machine refuses settings that make no sense", function()
	local state = VendingLogic.new()
	local function try(item, price, mode, limit)
		local ok, reason = VendingLogic.configure(state, {}, item, price, mode, limit, Stock.isKey)
		eq(ok, false)
		return reason
	end
	eq(try("banana", 5, "sell", 64), "item")
	eq(try(12, 5, "sell", 64), "item")
	eq(try("ingot_fe", 0, "sell", 64), "price")
	eq(try("ingot_fe", 1.5, "sell", 64), "price")
	eq(try("ingot_fe", 1e12, "sell", 64), "price")
	eq(try("ingot_fe", 5, "give", 64), "mode")
	eq(try("ingot_fe", 5, "buy", 0), "limit")
	eq(state.item, nil)
end)
test("choosing a different thing gives the old stock back to the owner", function()
	local state = selling("ingot_fe", 20, 12)
	local bag = { ingot_fe = 1 }
	eq(VendingLogic.configure(state, bag, "coal", 3, "sell", 64, Stock.isKey), true)
	eq(bag.ingot_fe, 13)
	eq(state.stock, 0)
	eq(state.item, "coal")
	-- changing only the price keeps the stock
	local other = selling("ingot_fe", 20, 12)
	eq(VendingLogic.configure(other, {}, "ingot_fe", 25, "sell", 64, Stock.isKey), true)
	eq(other.stock, 12)
	eq(other.price, 25)
end)
test("a visitor buys from a selling machine and the owner is paid", function()
	local state = selling("ingot_fe", 20, 10)
	local bag = {}
	local ok, _, visitor, owner = VendingLogic.purchase(state, bag, 100, 7, 4)
	eq(ok, true)
	eq(bag.ingot_fe, 4)
	eq(state.stock, 6)
	eq(visitor, 20)
	eq(owner, 87)
end)
test("a purchase fails whole when stock or coins are short", function()
	local state = selling("ingot_fe", 20, 3)
	local bag = {}
	local ok, reason, visitor, owner = VendingLogic.purchase(state, bag, 1000, 0, 4)
	eq(ok, false)
	eq(reason, "stock")
	ok, reason, visitor, owner = VendingLogic.purchase(state, bag, 59, 0, 3)
	eq(reason, "coins")
	eq(visitor, 59)
	eq(owner, 0)
	eq(state.stock, 3)
	eq(next(bag), nil)
	for _, n in BAD_AMOUNTS do
		ok, reason = VendingLogic.purchase(state, bag, 1e9, 0, n)
		eq(ok, false)
		eq(reason, "amount")
	end
	eq(state.stock, 3)
end)
test("a visitor sells to a buying machine and the owner pays", function()
	local state = buying("coal", 5, 20)
	local bag = { coal = 30 }
	local ok, _, visitor, owner = VendingLogic.supply(state, bag, 0, 1000, 12)
	eq(ok, true)
	eq(bag.coal, 18)
	eq(state.stock, 12)
	eq(visitor, 60)
	eq(owner, 940)
end)
test("a buying machine stops at its limit and at the owner's coins", function()
	local state = buying("coal", 5, 20)
	local bag = { coal = 100 }
	eq(VendingLogic.wanted(state, 1000), 20)
	eq(VendingLogic.wanted(state, 32), 6)
	local ok, reason = VendingLogic.supply(state, bag, 0, 1000, 21)
	eq(ok, false)
	eq(reason, "limit")
	ok, reason = VendingLogic.supply(state, bag, 0, 49, 10)
	eq(reason, "ownercoins")
	ok, reason = VendingLogic.supply(state, { coal = 2 }, 0, 1000, 3)
	eq(reason, "missing")
	eq(state.stock, 0)
	eq(bag.coal, 100)
	eq(VendingLogic.supply(state, bag, 0, 1000, 20), true)
	eq(VendingLogic.wanted(state, 1000), 0)
end)
test("a machine only works the way it is set", function()
	local seller, buyer, fresh = selling("coal", 5, 5), buying("coal", 5, 20), VendingLogic.new()
	local _, reason = VendingLogic.supply(seller, { coal = 5 }, 0, 1000, 1)
	eq(reason, "closed")
	_, reason = VendingLogic.purchase(buyer, {}, 1000, 0, 1)
	eq(reason, "closed")
	_, reason = VendingLogic.purchase(fresh, {}, 1000, 0, 1)
	eq(reason, "closed")
	eq(VendingLogic.wanted(seller, 1000), 0)
end)
test("a vending machine never creates or destroys anything", function()
	math.randomseed(11)
	for _ = 1, 400 do
		local ownerBag, visitorBag = { coal = math.random(1, 80) }, { coal = math.random(1, 80) }
		local ownerCoins, visitorCoins = math.random(0, 500), math.random(0, 500)
		local items = ownerBag.coal + visitorBag.coal
		local coins = ownerCoins + visitorCoins
		local state = VendingLogic.new()
		local mode = if math.random() < 0.5 then "sell" else "buy"
		VendingLogic.configure(
			state,
			ownerBag,
			"coal",
			math.random(1, 9),
			mode,
			math.random(1, 60),
			Stock.isKey
		)
		for _ = 1, 12 do
			local n = math.random(0, 40)
			local roll = math.random(1, 5)
			local _ok, _why
			if roll == 1 then
				VendingLogic.deposit(state, ownerBag, n)
			elseif roll == 2 then
				VendingLogic.withdraw(state, ownerBag, n)
			elseif roll == 3 then
				_ok, _why, visitorCoins, ownerCoins =
					VendingLogic.purchase(state, visitorBag, visitorCoins, ownerCoins, n)
			elseif roll == 4 then
				_ok, _why, visitorCoins, ownerCoins =
					VendingLogic.supply(state, visitorBag, visitorCoins, ownerCoins, n)
			else
				local other = if state.mode == "sell" then "buy" else "sell"
				VendingLogic.configure(
					state,
					ownerBag,
					"coal",
					math.random(1, 9),
					other,
					math.random(1, 60),
					Stock.isKey
				)
			end
			eq((ownerBag.coal or 0) + (visitorBag.coal or 0) + state.stock, items, "items")
			eq(ownerCoins + visitorCoins, coins, "coins")
			assert(ownerCoins >= 0 and visitorCoins >= 0 and state.stock >= 0, "something went negative")
			assert((ownerBag.coal or 1) > 0 and (visitorBag.coal or 1) > 0, "a zero count was left in a bag")
		end
	end
end)
test("stored machine settings are cleaned on load", function()
	local state =
		VendingLogic.sanitize({ item = "coal", price = 5, mode = "buy", stock = 12, limit = 30 }, Stock.isKey)
	eq(state.item, "coal")
	eq(state.price, 5)
	eq(state.mode, "buy")
	eq(state.stock, 12)
	eq(state.limit, 30)
	local bad = VendingLogic.sanitize(
		{ item = "banana", price = -1, mode = "x", stock = 1e9, limit = 0 },
		Stock.isKey
	)
	eq(bad.item, nil)
	eq(bad.price, 0)
	eq(bad.mode, "sell")
	eq(bad.stock, 0)
	eq(bad.limit, VendingLogic.DEFAULT_LIMIT)
	-- stock without a known item is dropped rather than turned into something else
	eq(VendingLogic.sanitize({ item = 5, stock = 40 }, Stock.isKey).stock, 0)
	eq(VendingLogic.sanitize("junk", Stock.isKey).item, nil)
	eq(VendingLogic.isReady(VendingLogic.sanitize({ item = "coal", price = "x" }, Stock.isKey)), false)
end)

T.done()
