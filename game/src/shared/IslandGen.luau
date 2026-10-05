--!strict
-- The island a new player starts on: a small grassy slab with dirt and stone under it, and two trees.
local IslandGen = {}

export type Block = { x: number, y: number, z: number, id: string }

-- Radius of each layer, top first. The edge wobbles a little so the island is not a perfect disc.
local LAYERS = {
	{ y = 0, id = "grass", radius = 7.3 },
	{ y = -1, id = "dirt", radius = 6.4 },
	{ y = -2, id = "stone", radius = 5.2 },
	{ y = -3, id = "stone", radius = 3.6 },
	{ y = -4, id = "stone", radius = 2.0 },
}

local function wobble(x: number, z: number): number
	return 0.55 * math.sin(x * 1.3 + z * 0.7) + 0.35 * math.cos(z * 1.9 - x * 0.4)
end

local function tree(out: { Block }, x: number, z: number, height: number)
	for y = 1, height do
		table.insert(out, { x = x, y = y, z = z, id = "log" })
	end
	for dy = 0, 1 do
		for dx = -1, 1 do
			for dz = -1, 1 do
				if not (dx == 0 and dz == 0 and dy == 0) then
					table.insert(out, { x = x + dx, y = height + dy, z = z + dz, id = "leaves" })
				end
			end
		end
	end
	table.insert(out, { x = x, y = height + 2, z = z, id = "leaves" })
end

function IslandGen.generate(): { Block }
	local out: { Block } = {}
	for _, layer in LAYERS do
		local reach = math.ceil(layer.radius) + 1
		for x = -reach, reach do
			for z = -reach, reach do
				if math.sqrt(x * x + z * z) + wobble(x, z) <= layer.radius then
					table.insert(out, { x = x, y = layer.y, z = z, id = layer.id })
				end
			end
		end
	end
	tree(out, -4, -3, 3)
	tree(out, 4, 3, 4)
	return out
end

-- Cell the player stands on when they arrive.
IslandGen.SPAWN = { x = 0, y = 1, z = 0 }

return IslandGen
