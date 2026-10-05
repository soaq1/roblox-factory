--!strict
-- What tools do. A tool is a bag item named "<kind>_<tier>" (pick_wood, sword_dia). Holding a
-- better one makes the work it is for go faster; nothing is ever impossible bare-handed on the
-- island, only slow. In the mine, the richer ores do need a good enough pickaxe.
-- Every number here is a placeholder to be tuned by play.
local ToolLogic = {}

export type Bag = { [string]: number }
export type Node = { item: string, hardness: number, minRank: number, core: string?, respawn: number }

ToolLogic.TIERS = { "wood", "stone", "iron", "steel", "gold", "dia" } -- weakest first; rank 1 to 6
ToolLogic.KINDS = { "pick", "axe", "shovel", "hoe", "sword" }

-- How much one swing does, by the rank of the right tool. The first entry is rank 0: bare hands
-- or the wrong tool.
local POWER = { 1, 2, 3, 4, 6, 8, 12 }
-- What one hit on a monster takes off, by sword rank, again starting at rank 0.
local DAMAGE = { 2, 5, 7, 10, 14, 18, 25 }

ToolLogic.CORE_CHANCE = 0.01 -- chance that mining a node also gives its vein core
ToolLogic.PART_CHANCE = 0.05 -- chance that a slain monster drops a monster part

-- The rank of the best tool of one kind in the bag, 0 if there is none, and that tool's key.
function ToolLogic.best(bag: Bag, kind: string): (number, string?)
	for rank = #ToolLogic.TIERS, 1, -1 do
		local key = kind .. "_" .. ToolLogic.TIERS[rank]
		if (bag[key] or 0) >= 1 then
			return rank, key
		end
	end
	return 0, nil
end

-- The kind and rank of a tool, or nil if the item is not one ("pick_iron" -> "pick", 3).
function ToolLogic.parse(itemId: any): (string?, number)
	if type(itemId) ~= "string" then
		return nil, 0
	end
	local kind, tier = string.match(itemId, "^(%a+)_(%a+)$")
	if not kind or not tier then
		return nil, 0
	end
	local rank = table.find(ToolLogic.TIERS, tier)
	if rank and table.find(ToolLogic.KINDS, kind) then
		return kind, rank
	end
	return nil, 0
end

-- The bag to judge a swing by. Only the tool in the hand counts, not the best one carried, so
-- this is a bag holding just that tool: empty if the hand holds no tool, or one the player does
-- not have (`free` is creative mode, where every tool is to hand).
function ToolLogic.inHand(bag: Bag, held: any, free: boolean): Bag
	local kind = ToolLogic.parse(held)
	if kind and (free or (bag[held] or 0) >= 1) then
		return { [held] = 1 }
	end
	return {}
end

-- Ground a hoe turns into farmland.
local TILLABLE = { dirt = true, grass = true }

-- Does swinging this tool at this block till it into farmland rather than break it?
function ToolLogic.tills(held: any, blockId: string): boolean
	return (ToolLogic.parse(held)) == "hoe" and TILLABLE[blockId] == true
end

-- A hoe never digs up a field: swinging one at farmland does nothing. Without this, holding the
-- button a moment too long after tilling would break the farmland that was just made.
function ToolLogic.spares(held: any, blockId: string): boolean
	return (ToolLogic.parse(held)) == "hoe" and blockId == "farmland"
end

-- How many tools of any kind a bag holds.
function ToolLogic.count(bag: Bag): number
	local total = 0
	for key, n in bag do
		if ToolLogic.parse(key) then
			total += n
		end
	end
	return total
end

function ToolLogic.power(rank: number): number
	return POWER[math.clamp(rank, 0, #ToolLogic.TIERS) + 1]
end

-- The tool each block is worked with, and how hard it is. Anything not listed takes DEFAULT.
local SHOVEL, AXE, PICK = "shovel", "axe", "pick"
type Block = { tool: string?, hardness: number }
local DEFAULT: Block = { hardness = 4 }
local BLOCKS: { [string]: Block } = {
	grass = { tool = SHOVEL, hardness = 3 },
	dirt = { tool = SHOVEL, hardness = 3 },
	farmland = { tool = SHOVEL, hardness = 3 },
	sand = { tool = SHOVEL, hardness = 3 },
	gravel = { tool = SHOVEL, hardness = 4 },
	clay = { tool = SHOVEL, hardness = 4 },
	log = { tool = AXE, hardness = 6 },
	planks = { tool = AXE, hardness = 5 },
	leaves = { hardness = 1 },
	glass = { hardness = 2 },
	stone = { tool = PICK, hardness = 8 },
	stone_bricks = { tool = PICK, hardness = 8 },
	bricks = { tool = PICK, hardness = 8 },
	concrete = { tool = PICK, hardness = 8 },
	asphalt = { tool = PICK, hardness = 8 },
	quartz = { tool = PICK, hardness = 8 },
	ore_coal = { tool = PICK, hardness = 10 },
	ore_cu = { tool = PICK, hardness = 10 },
	ore_fe = { tool = PICK, hardness = 10 },
	ore_au = { tool = PICK, hardness = 10 },
	ore_dia = { tool = PICK, hardness = 10 },
	block_fe = { tool = PICK, hardness = 12 },
	block_cu = { tool = PICK, hardness = 12 },
	block_steel = { tool = PICK, hardness = 12 },
	block_au = { tool = PICK, hardness = 12 },
	block_dia = { tool = PICK, hardness = 12 },
	block_coal = { tool = PICK, hardness = 12 },
	tread = { tool = PICK, hardness = 12 },
	grating = { tool = PICK, hardness = 12 },
	cloth_white = { hardness = 2 },
	cloth_red = { hardness = 2 },
	cloth_yellow = { hardness = 2 },
	cloth_green = { hardness = 2 },
	cloth_blue = { hardness = 2 },
}

-- The kind of tool that speeds up breaking a block, if any.
function ToolLogic.blockTool(blockId: string): string?
	local entry = BLOCKS[blockId]
	return if entry then entry.tool else nil
end

-- How many swings a block takes with what is in the bag. Always at least one.
function ToolLogic.blockHits(blockId: string, bag: Bag): number
	local entry = BLOCKS[blockId] or DEFAULT
	local rank = 0
	if entry.tool then
		rank = ToolLogic.best(bag, entry.tool)
	end
	return math.max(1, math.ceil(entry.hardness / ToolLogic.power(rank)))
end

-- Machines are lifted with a pickaxe, a few swings each, the way a block is. Plants come up at a
-- touch; belts and other small fittings are lighter than a full machine. Placeholder numbers.
local MACHINE_HARDNESS = { plant = 1, light = 4, heavy = 8 }
local LIGHT = { belt = true, ramp = true, chute = true, sign = true, signal = true }

-- How hard a machine is to lift, from its definition.
function ToolLogic.machineHardness(def: { cost: string?, behavior: string? }): number
	if def.cost then
		return MACHINE_HARDNESS.plant
	elseif def.behavior and LIGHT[def.behavior] then
		return MACHINE_HARDNESS.light
	end
	return MACHINE_HARDNESS.heavy
end

-- How many swings a machine of that hardness takes with what is in the bag. A pickaxe is the
-- tool for it; anything else counts as the wrong tool. Always at least one.
function ToolLogic.machineHits(hardness: number, bag: Bag): number
	local rank = ToolLogic.best(bag, "pick")
	return math.max(1, math.ceil(hardness / ToolLogic.power(rank)))
end

-- The things that can be mined in the hub. `minRank` is the weakest pickaxe that works at all
-- (0 means bare hands will do). Gold and diamond have no vein core here.
ToolLogic.NODES = {
	stone = { item = "stone", hardness = 6, minRank = 0, core = "core_stone", respawn = 6 },
	coal = { item = "coal", hardness = 8, minRank = 1, core = "core_coal", respawn = 10 },
	ore_cu = { item = "ore_cu", hardness = 10, minRank = 1, core = "core_cu", respawn = 12 },
	ore_fe = { item = "ore_fe", hardness = 12, minRank = 1, core = "core_fe", respawn = 14 },
	ore_au = { item = "ore_au", hardness = 16, minRank = 3, respawn = 30 },
	ore_dia = { item = "ore_dia", hardness = 24, minRank = 4, respawn = 60 },
} :: { [string]: Node }

-- How much one swing takes off a node's hardness, or nil if the pickaxe in the bag is too weak.
function ToolLogic.nodeSwing(kind: string, bag: Bag): number?
	local node = ToolLogic.NODES[kind]
	if not node then
		return nil
	end
	local rank = ToolLogic.best(bag, "pick")
	if rank < node.minRank then
		return nil
	end
	return ToolLogic.power(rank)
end

-- The name of the weakest pickaxe that can mine a node, for telling the player what to bring.
function ToolLogic.nodeNeeds(kind: string): string?
	local node = ToolLogic.NODES[kind]
	if not node or node.minRank < 1 then
		return nil
	end
	return "pick_" .. ToolLogic.TIERS[node.minRank]
end

-- The vein core a mined node also gives. `roll` is a random number from 0 up to 1.
function ToolLogic.rollCore(kind: string, roll: number): string?
	local node = ToolLogic.NODES[kind]
	if node and node.core and roll < ToolLogic.CORE_CHANCE then
		return node.core
	end
	return nil
end

-- What one hit does to a monster with the best sword in the bag.
function ToolLogic.damage(bag: Bag): number
	local rank = ToolLogic.best(bag, "sword")
	return DAMAGE[rank + 1]
end

function ToolLogic.rollPart(roll: number): boolean
	return roll < ToolLogic.PART_CHANCE
end

-- Counts swings at one target. A swing sooner than `gap` after the last is ignored (it would be
-- an auto-clicker), and a pause longer than `keep`, or a change of target, starts over.
export type Swing = { target: string, hits: number, at: number }

-- Returns the swing state to keep and how many swings have landed on `target` (0 if this one was
-- ignored for coming too soon).
function ToolLogic.swing(
	last: Swing?,
	target: string,
	now: number,
	gap: number,
	keep: number
): (Swing, number)
	if last and now - last.at < gap then
		return last, 0
	end
	if not last or last.target ~= target or now - last.at > keep then
		local fresh: Swing = { target = target, hits = 1, at = now }
		return fresh, 1
	end
	last.hits += 1
	last.at = now
	return last, last.hits
end

return ToolLogic
