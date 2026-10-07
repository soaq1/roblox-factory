--!nocheck
-- What the hand can do with the thing it holds, apart from swinging a tool (that is ToolLogic):
-- which loose item a held thing is let go as, which slot a thing looked at belongs in, which way
-- a dragged belt faces, and how to tell which block a placed part is from the way it looks.
-- Definitions and the bag rules are passed in, so this runs outside Roblox.
local HandLogic = {}

-- The loose item that Q lets go of for a hotbar entry, or nil if the entry has no loose form.
-- An "item:<id>" entry is that item. A block that is also an item (log, stone, ore), or that is
-- laid from one (dirt from a clod), is let go as that item; so is a plant, as its seed. In
-- survival the bag must hold it; `free` is creative mode.
function HandLogic.looseForm(Defs, Stock, entry: string, bag: { [string]: number }, free: boolean): string?
	local item = Defs.itemOf(entry)
	if item then
		return item
	end
	local first: string? = nil
	for _, key in Stock.placeCost(entry) do
		if Defs.Items[key] then
			if (bag[key] or 0) >= 1 then
				return key
			end
			first = first or key
		end
	end
	return if free then first else nil
end

-- Can the bag pay for placing this entry? Everything is to hand in creative mode.
function HandLogic.canSupply(Stock, entry: string, bag: { [string]: number }, free: boolean): boolean
	if free then
		return true
	end
	for _, key in Stock.placeCost(entry) do
		if (bag[key] or 0) >= 1 then
			return true
		end
	end
	return false
end

-- Where the thing looked at goes: the slot that already holds it ("select"), else the current
-- slot if the bag can supply it ("assign"), else nowhere ("none").
function HandLogic.pick(
	Stock,
	slots: { string },
	entry: string,
	bag: { [string]: number },
	free: boolean
): (string, number?)
	local index = table.find(slots, entry)
	if index then
		return "select", index
	end
	if HandLogic.canSupply(Stock, entry, bag, free) then
		return "assign", nil
	end
	return "none", nil
end

-- The facing (0..3 = +X, +Z, -X, -Z) of a belt laid one cell further along a drag, or nil when
-- the step is not to a cell straight ahead, behind or beside on the same level.
function HandLogic.dragDir(dx: number, dy: number, dz: number): number?
	if dy ~= 0 or math.abs(dx) + math.abs(dz) ~= 1 then
		return nil
	end
	if dx == 1 then
		return 0
	elseif dz == 1 then
		return 1
	elseif dx == -1 then
		return 2
	end
	return 3
end

-- A block is drawn with a thin cap when its top differs enough from its sides. (The same test
-- the server uses when it builds the block.)
local function capOf(def): { number }?
	local c, t = def.color, def.top
	if math.abs(t[1] - c[1]) + math.abs(t[2] - c[2]) + math.abs(t[3] - c[3]) > 60 then
		return t
	end
	return nil
end

local function same(a: { number }?, b: { number }?): boolean
	if not a or not b then
		return a == b
	end
	return a[1] == b[1] and a[2] == b[2] and a[3] == b[3]
end

-- Which block a placed part is, told from its side colour and its cap (nil if it has none).
-- Placed blocks carry no name, so their look is all there is to go on.
function HandLogic.blockByLook(Defs, side: { number }, cap: { number }?): string?
	local ids = {}
	for id in Defs.Blocks do
		table.insert(ids, id)
	end
	table.sort(ids)
	for _, id in ids do
		local def = Defs.Blocks[id]
		if same(def.color, side) and same(capOf(def), cap) then
			return id
		end
	end
	return nil
end

-- A standing character, as a box round the middle of its body (studs): half its width, how far it
-- reaches below and above that middle, and how much of the box's edge is let off, so that the cell
-- a player stands on, or one they only brush against, does not count.
local BODY_HALF, BODY_DOWN, BODY_UP, BODY_SLACK = 1.0, 3.0, 2.2, 0.25

-- Would a block in the cell centred at (cx, cy, cz) be inside a character whose body is centred at
-- (rx, ry, rz)? Nothing is placed where someone stands: it would shut them in or throw them aside.
function HandLogic.bodyInCell(
	cx: number,
	cy: number,
	cz: number,
	cell: number,
	rx: number,
	ry: number,
	rz: number
): boolean
	local half = cell / 2
	local side = BODY_HALF - BODY_SLACK
	if math.abs(rx - cx) >= half + side or math.abs(rz - cz) >= half + side then
		return false
	end
	local low, high = ry - BODY_DOWN + BODY_SLACK, ry + BODY_UP - BODY_SLACK
	return low < cy + half and high > cy - half
end

-- The cells a machine placed at (x, y, z) covers, as "x,y,z" keys given by `keyOf`.
function HandLogic.covered(Grid, def, x: number, y: number, z: number, dir: number): { string }
	local keys = {}
	for layer = 0, (def.sy or 1) - 1 do
		for _, cell in Grid.footprint(x, z, dir, def.sx or 1, def.sz or 1) do
			table.insert(keys, Grid.key(cell[1], y + layer, cell[2]))
		end
	end
	return keys
end

-- Where a belt's things come in and go out, in the same form as a machine's ports. Belts have
-- none listed because nothing is swallowed, but the outline still shows which way they carry.
function HandLogic.beltPorts(shape: string?): { { side: string, kind: string, off: number } }
	local out = if shape == "right" then "S" elseif shape == "left" then "N" else "E"
	return { { side = "W", kind = "in", off = 0 }, { side = out, kind = "out", off = 0 } }
end

return HandLogic
