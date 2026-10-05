-- The reasoning behind the bag, crafting and trade screens:  lune run tests/screens_test.luau
local T = require("./harness")
local Defs = require("../src/shared/Defs")
local Recipes = require("../src/shared/Recipes")
local CraftLogic = require("../src/shared/CraftLogic")
local Stock = (require("../src/shared/Stock") :: any)(Defs)
local ScreenLogic = require("../src/shared/ScreenLogic")

local test, eq = T.test, T.eq

test("craft recipes are grouped by bench, bag first, and every recipe is in exactly one group", function()
	local groups = ScreenLogic.groups(Recipes.craft, "bench")
	eq(groups[1].name, "bag")
	local seen, count = {}, 0
	for _, group in groups do
		assert(#group.indexes > 0, "empty group " .. group.name)
		for _, index in group.indexes do
			assert(not seen[index], "recipe listed twice")
			seen[index] = true
			count += 1
			eq(Recipes.craft[index].bench, group.name)
		end
	end
	eq(count, #Recipes.craft)
end)
test("groups keep the recipes' own order and put known benches before unknown ones", function()
	local groups = ScreenLogic.groups({
		{ bench = "zzz" },
		{ bench = "machine" },
		{ bench = "bag" },
		{ bench = "machine" },
		{ bench = "aaa" },
	}, "bench")
	eq(groups[1].name, "bag")
	eq(groups[2].name, "machine")
	eq(groups[2].indexes[1], 2)
	eq(groups[2].indexes[2], 4)
	eq(groups[3].name, "aaa")
	eq(groups[4].name, "zzz")
end)
test("hand work is grouped by station", function()
	local groups = ScreenLogic.groups(Recipes.hand, "station")
	local count = 0
	for _, group in groups do
		for _, index in group.indexes do
			eq(Recipes.hand[index].station, group.name)
			count += 1
		end
	end
	eq(count, #Recipes.hand)
end)

test("the most times something can be made is set by the scarcest ingredient", function()
	eq(ScreenLogic.maxTimes({ plate_fe = 9, rod_fe = 5 }, { plate_fe = 2, rod_fe = 2 }, 999), 2)
	eq(ScreenLogic.maxTimes({ plate_fe = 9 }, { plate_fe = 2, rod_fe = 2 }, 999), 0)
	eq(ScreenLogic.maxTimes({ plank = 100000 }, { plank = 8 }, 999), 999)
	eq(ScreenLogic.maxTimes({}, {}, 5), 5)
end)
test("the most that can be made really can be made, and one more cannot", function()
	local benches = { part = 1 }
	for _, recipe in Recipes.craft do
		if recipe.bench == "part" and recipe.tier <= 1 then
			local bag = {}
			for key, n in recipe.ins do
				bag[key] = n * 3 + 1
			end
			local most = ScreenLogic.maxTimes(bag, recipe.ins, CraftLogic.MAX_TIMES)
			eq(most, 3)
			eq(CraftLogic.blocked(bag, recipe, benches, most), nil)
			eq(CraftLogic.blocked(bag, recipe, benches, most + 1), "missing")
		end
	end
end)

local function handSmelt()
	for _, recipe in Recipes.hand do
		if recipe.station == "hand_furnace" and recipe.ins.ore_fe == 1 and recipe.outs.ingot_fe then
			return recipe
		end
	end
	error("no hand smelting recipe")
end
test("hand work is limited by fuel as well as by ingredients", function()
	local benches = { hand_furnace = 1 }
	-- one coal pays for four smelts
	eq(ScreenLogic.maxHand(CraftLogic, { ore_fe = 10, coal = 1 }, handSmelt(), benches, Recipes.fuel, 999), 4)
	eq(ScreenLogic.maxHand(CraftLogic, { ore_fe = 3, coal = 5 }, handSmelt(), benches, Recipes.fuel, 999), 3)
	eq(ScreenLogic.maxHand(CraftLogic, { ore_fe = 10 }, handSmelt(), benches, Recipes.fuel, 999), 0)
	eq(ScreenLogic.maxHand(CraftLogic, { ore_fe = 10, coal = 9 }, handSmelt(), {}, Recipes.fuel, 999), 0)
end)
test("working out the most hand work never changes the bag", function()
	local bag = { ore_fe = 10, coal = 2 }
	ScreenLogic.maxHand(CraftLogic, bag, handSmelt(), { hand_furnace = 1 }, Recipes.fuel, 999)
	eq(bag.ore_fe, 10)
	eq(bag.coal, 2)
	eq(bag.ingot_fe, nil)
end)
test("the most hand work is exact: it works, and one more does not", function()
	local benches = { hand_furnace = 1 }
	for _, coal in { 1, 2, 3, 7 } do
		local bag = { ore_fe = 50, coal = coal, log = 3 }
		local most = ScreenLogic.maxHand(CraftLogic, bag, handSmelt(), benches, Recipes.fuel, 999)
		eq((CraftLogic.hand(table.clone(bag), handSmelt(), benches, most, Recipes.fuel, 0)), true)
		eq((CraftLogic.hand(table.clone(bag), handSmelt(), benches, most + 1, Recipes.fuel, 0)), false)
	end
end)

test("benches count only within range, at the island's tier for that kind", function()
	local seen = {
		{ kind = "basic", distance = 4 },
		{ kind = "machine", distance = 15 },
		{ kind = "part", distance = 15.1 },
		{ kind = "hand_furnace", distance = 2 },
		{ kind = "basic", distance = 30 },
	}
	local benches = ScreenLogic.benchesNear(seen, { basic = 3, part = 2 }, 15)
	eq(benches.basic, 3)
	eq(benches.machine, 1)
	eq(benches.part, nil)
	eq(benches.hand_furnace, 1)
	eq(next(ScreenLogic.benchesNear({}, {}, 15)), nil)
end)

test("a bag key becomes the right thing on the hotbar", function()
	local smelter = ScreenLogic.forms(Defs, Stock, "smelter")
	eq(smelter.place, "smelter")
	eq(smelter.drop, nil)
	local planks = ScreenLogic.forms(Defs, Stock, "block:planks")
	eq(planks.place, "planks")
	eq(planks.drop, nil)
	local ingot = ScreenLogic.forms(Defs, Stock, "ingot_fe")
	eq(ingot.place, nil)
	eq(ingot.drop, "item:ingot_fe")
	-- a log is both a block and a thing to feed a sawmill
	local log = ScreenLogic.forms(Defs, Stock, "log")
	eq(log.place, "log")
	eq(log.drop, "item:log")
	eq(ScreenLogic.forms(Defs, Stock, "sapling").place, "plant_sapling")
	eq(ScreenLogic.forms(Defs, Stock, "seed").place, "crop_wheat_1")
	eq(ScreenLogic.forms(Defs, Stock, "dirt_clod").place, "dirt")
	local nothing = ScreenLogic.forms(Defs, Stock, "banana")
	eq(nothing.place, nil)
	eq(nothing.drop, nil)
end)
test("whatever the bag screen offers to place, the bag key can pay for", function()
	local keys = {}
	for id in Defs.Items do
		table.insert(keys, id)
	end
	for id in Defs.Machines do
		table.insert(keys, id)
	end
	for id in Defs.Blocks do
		table.insert(keys, "block:" .. id)
	end
	for _, key in keys do
		local forms = ScreenLogic.forms(Defs, Stock, key)
		if forms.place then
			assert(Defs.isPlaceable(forms.place), key .. " offers unplaceable " .. forms.place)
			assert(table.find(Stock.placeCost(forms.place), key), key .. " cannot pay for " .. forms.place)
			assert(
				not Defs.Machines[forms.place] or not Defs.Machines[forms.place].hidden,
				key .. " offers a hidden machine"
			)
		end
		if forms.drop then
			assert(Defs.itemOf(forms.drop) == key, key .. " drops as the wrong thing")
		end
		-- Hidden machines and planted forms are never held as themselves.
		local machine = Defs.Machines[key]
		local neverHeld = machine and (machine.hidden or machine.cost)
		assert(neverHeld or forms.place or forms.drop, key .. " cannot be used at all")
	end
end)

test("the hotbar count adds up everything that can pay for the slot", function()
	local bag = { log = 3, ["block:log"] = 2, sapling = 4, smelter = 1, dirt_clod = 6 }
	eq(ScreenLogic.held(Defs, Stock, bag, "log"), 5)
	eq(ScreenLogic.held(Defs, Stock, bag, "item:log"), 3)
	eq(ScreenLogic.held(Defs, Stock, bag, "plant_sapling"), 4)
	eq(ScreenLogic.held(Defs, Stock, bag, "smelter"), 1)
	eq(ScreenLogic.held(Defs, Stock, bag, "dirt"), 6)
	eq(ScreenLogic.held(Defs, Stock, bag, "belt"), 0)
	eq(ScreenLogic.held(Defs, Stock, bag, "banana"), 0)
end)

test("the bag is listed machines first, then blocks, then items", function()
	local list = ScreenLogic.sorted(
		Defs,
		Stock,
		{ ingot_fe = 4, ["block:planks"] = 2, smelter = 1, coal = 9, belt = 3 }
	)
	eq(#list, 5)
	eq(list[1].rank, 1)
	eq(list[2].rank, 1)
	eq(list[3].key, "block:planks")
	eq(list[4].rank, 3)
	eq(list[5].rank, 3)
	local kinds, total = ScreenLogic.totals({ ingot_fe = 4, coal = 9 })
	eq(kinds, 2)
	eq(total, 13)
end)
test("the bag's order does not depend on the order it was filled in", function()
	local a = ScreenLogic.sorted(Defs, Stock, { ingot_fe = 1, coal = 1, ore_fe = 1, log = 1 })
	local b = ScreenLogic.sorted(Defs, Stock, { log = 1, ore_fe = 1, coal = 1, ingot_fe = 1 })
	for i = 1, 4 do
		eq(a[i].key, b[i].key)
	end
end)

test("typed amounts are whole numbers within what is held", function()
	eq(ScreenLogic.amount("12", 50), 12)
	eq(ScreenLogic.amount("120", 50), 50)
	eq(ScreenLogic.amount("", 50), 0)
	eq(ScreenLogic.amount("abc", 50), 0)
	eq(ScreenLogic.amount("-3", 50), 0)
	eq(ScreenLogic.amount("2.9", 50), 2)
	eq(ScreenLogic.amount("nan", 50), 0)
	eq(ScreenLogic.amount(7, 5), 5)
	eq(ScreenLogic.amount(nil, 5), 0)
	eq(ScreenLogic.amount("4", -1), 0)
end)

local function snap(aOffer, aCoins, aReady, bOffer, bCoins, bReady)
	return {
		a = { offer = aOffer, coins = aCoins, ready = aReady },
		b = { offer = bOffer, coins = bCoins, ready = bReady },
	}
end
test("a change by the other side is noticed, a change of my own is not", function()
	local before = snap({ ingot_fe = 4 }, 0, true, { core_fe = 1 }, 0, true)
	eq(ScreenLogic.otherChanged(before, snap({ ingot_fe = 4 }, 0, false, {}, 0, false), "a"), true)
	eq(
		ScreenLogic.otherChanged(before, snap({ ingot_fe = 4 }, 0, false, { core_fe = 1 }, 5, false), "a"),
		true
	)
	eq(
		ScreenLogic.otherChanged(
			before,
			snap({ ingot_fe = 4 }, 0, false, { core_fe = 1, coal = 1 }, 0, false),
			"a"
		),
		true
	)
	eq(
		ScreenLogic.otherChanged(before, snap({ ingot_fe = 1 }, 0, false, { core_fe = 1 }, 0, false), "a"),
		false
	)
	eq(
		ScreenLogic.otherChanged(before, snap({ ingot_fe = 1 }, 0, false, { core_fe = 1 }, 0, false), "b"),
		true
	)
	eq(ScreenLogic.otherChanged(nil, before, "a"), false)
end)
test("being un-readied is reported only when I was ready and the other side changed", function()
	local before = snap({ ingot_fe = 4 }, 0, true, { core_fe = 1 }, 0, true)
	eq(ScreenLogic.wasUnreadied(before, snap({ ingot_fe = 4 }, 0, false, {}, 0, false), "a"), true)
	-- I changed my own offer: nothing to warn me about
	eq(
		ScreenLogic.wasUnreadied(before, snap({ ingot_fe = 1 }, 0, false, { core_fe = 1 }, 0, false), "a"),
		false
	)
	-- I was not ready anyway
	local idle = snap({ ingot_fe = 4 }, 0, false, { core_fe = 1 }, 0, true)
	eq(ScreenLogic.wasUnreadied(idle, snap({ ingot_fe = 4 }, 0, false, {}, 0, false), "a"), false)
	-- I un-readied myself
	eq(
		ScreenLogic.wasUnreadied(before, snap({ ingot_fe = 4 }, 0, false, { core_fe = 1 }, 0, true), "a"),
		false
	)
end)

T.done()
