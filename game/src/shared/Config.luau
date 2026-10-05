--!strict
-- Numbers that shape how the game feels. Change them here, nowhere else.
return {
	CELL = 3, -- studs per grid cell
	REACH = 40, -- how far from the character a cell can be edited, in studs
	MAX_COORD = 400, -- cells may not be further than this from the island origin
	ISLAND_SPACING = 4096, -- studs between neighbouring islands in one server

	BELT_SPEED = 5, -- studs per second
	EXTRACT_INTERVAL = 2.0, -- seconds between items from one extractor
	MACHINE_BUFFER = 16, -- most of one ingredient a machine holds
	MACHINE_OUT = 8, -- finished items a machine holds before it pauses
	START_ITEMS = { pick_wood = 1 }, -- what a new player holds
	START_COINS = 10000, -- what a new player begins with (a placeholder amount)
	START_MODE = "survival", -- "creative": everything is free; "survival": only what is in the bag
	ALLOW_MODE_SWITCH = true, -- the /mode command; a test convenience, to be removed before release
	DAY_MINUTES = 20, -- real minutes for one in-game day; solar panels follow the sun
	BENCH_RANGE = 15, -- studs from a workbench within which it can be used
	SAPLING_SECONDS = 45, -- time for a sapling to become a tree
	CROP_SECONDS = 60, -- time for a crop to ripen

	MAX_STACK = 64, -- items one loose stack can hold
	MAX_LOOSE_ITEMS = 600, -- loose stacks allowed before the oldest are cleared
	PICKUP_RANGE = 10,

	MACHINE_TICK = 0.2, -- seconds between machine updates
	AUTOSAVE_SECONDS = 60,
	RATE_PER_SECOND = 25, -- edit requests a player may send per second
}
