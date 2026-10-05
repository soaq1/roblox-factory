-- What the hub's merchants sell and buy, in coins for one.
--
-- EVERY NUMBER HERE IS A PLACEHOLDER. They exist so the shop can be tried; the developer sets the
-- real ones. Changing a number, or adding or removing a line, needs no other change.
--
-- The rules these tables follow (tests/shop_test.luau checks them):
--   * The game SELLS only seeds, saplings and decoration blocks. Never a machine, a tool, or
--     anything a recipe uses, so coins cannot buy progress from the game.
--   * Merchants BUY crops, food, minerals, ingots and small parts.
--   * Nothing is bought back for as much as it is sold for.
-- A key is an item id, or "block:<id>" for a block.
local Prices = {}

Prices.sells = {
	farmer = {
		seed = 10,
		sapling = 50,
	},
	builder = {
		["block:quartz"] = 40,
		["block:stone_bricks"] = 30,
		["block:bricks"] = 30,
		["block:cloth_white"] = 25,
		["block:cloth_red"] = 25,
		["block:cloth_yellow"] = 25,
		["block:cloth_green"] = 25,
		["block:cloth_blue"] = 25,
	},
}

Prices.buys = {
	farmer = {
		wheat = 6,
		cotton = 8,
		oilseed = 5,
	},
	cook = {
		flour = 8,
		dough = 6,
		bread = 30,
	},
	miner = {
		-- minerals
		stone = 1,
		gravel = 1,
		sand = 2,
		clay = 3,
		coal = 4,
		ore_cu = 5,
		ore_fe = 6,
		ore_au = 40,
		ore_dia = 150,
		diamond = 400,
		-- ingots
		ingot_cu = 12,
		ingot_fe = 14,
		ingot_steel = 70,
		ingot_au = 90,
		ingot_alloy = 80,
		-- small parts
		plate_cu = 14,
		rod_cu = 7,
		plate_fe = 16,
		rod_fe = 8,
		coil = 7,
		bolt = 2,
		gear = 20,
	},
}

return Prices
