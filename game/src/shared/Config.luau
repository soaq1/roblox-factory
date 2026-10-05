--!strict
-- Numbers that shape how the game feels. Change them here, nowhere else.
return {
	CELL = 3, -- studs per grid cell
	REACH = 40, -- how far from the character a cell can be edited, in studs
	MAX_COORD = 400, -- cells may not be further than this from the island origin
	ISLAND_SPACING = 4096, -- studs between neighbouring islands in one server

	BELT_SPEED = 5, -- studs per second
	EXTRACT_INTERVAL = 2.0, -- seconds between items from one extractor
	SMELT_TIME = 3.0, -- seconds per ingot
	FUEL_PER_COAL = 4, -- ingots one coal can smelt
	SMELTER_MAX_FUEL = 16,
	SMELTER_MAX_ORE = 8,
	SMELTER_MAX_OUT = 4,

	MAX_STACK = 64, -- items one loose stack can hold
	MAX_LOOSE_ITEMS = 600, -- loose stacks allowed before the oldest are cleared
	PICKUP_RANGE = 10,

	MACHINE_TICK = 0.2, -- seconds between machine updates
	AUTOSAVE_SECONDS = 60,
	RATE_PER_SECOND = 25, -- edit requests a player may send per second
}
