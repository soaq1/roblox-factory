--!strict
-- The shape of a tree, worked out from a seed number. The same seed always gives the same tree,
-- so a tree looks the same after the island is saved and loaded again. Trees differ a little from
-- one another, never a lot; now and then a sapling grows into a giant instead.
--
-- Everything is in studs, measured from the middle of the ground under the trunk, y upward.
-- A tree is not made of blocks: it is a trunk that leans and forks, with a mass of leaves at the
-- end of each branch. It keeps the cells its trunk and leaves pass through, so nothing can be
-- built into it, and it will not grow where those cells are already taken.
-- Every number here is a placeholder to be tuned by eye.
local TreeGen = {}

TreeGen.CELL = 3
TreeGen.GIANT_CHANCE = 0.03 -- how often a sapling becomes a giant
local GIANT_SCALE = 2.6
local FLAT = 0.72 -- leaf masses are wider than they are tall
local SEGMENTS = 4

export type Limb = {
	ax: number,
	ay: number,
	az: number,
	bx: number,
	by: number,
	bz: number,
	r: number,
	trunk: boolean,
}
-- One angular lump of leaves: a box at a place, with a size, turned by three angles, in one of
-- three shades of green.
export type Lump = {
	x: number,
	y: number,
	z: number,
	sx: number,
	sy: number,
	sz: number,
	rx: number,
	ry: number,
	rz: number,
	shade: number,
}
export type Tree = {
	seed: number,
	giant: boolean,
	height: number,
	logs: number,
	hardness: number,
	limbs: { Limb },
	lumps: { Lump },
	cells: { { number } }, -- cells kept, as steps from the cell the trunk stands in; that cell is first
}

-- A small repeatable random source (Park-Miller). Luau's own is not repeatable across places.
local function source(seed: number): () -> number
	local state = math.floor(math.abs(seed)) % 2147483646 + 1
	local function roll(): number
		state = (state * 48271) % 2147483647
		return state / 2147483647
	end
	-- The first few numbers out of a small seed are all close to zero; throw them away.
	for _ = 1, 4 do
		roll()
	end
	return roll
end

local function between(roll: () -> number, lo: number, hi: number): number
	return lo + (hi - lo) * roll()
end

-- Distance from a point to the stretch between two points.
local function toStretch(
	px: number,
	py: number,
	pz: number,
	ax: number,
	ay: number,
	az: number,
	bx: number,
	by: number,
	bz: number
): number
	local dx, dy, dz = bx - ax, by - ay, bz - az
	local len2 = dx * dx + dy * dy + dz * dz
	local t = 0
	if len2 > 0 then
		t = math.clamp(((px - ax) * dx + (py - ay) * dy + (pz - az) * dz) / len2, 0, 1)
	end
	local cx, cy, cz = ax + dx * t, ay + dy * t, az + dz * t
	return math.sqrt((px - cx) ^ 2 + (py - cy) ^ 2 + (pz - cz) ^ 2)
end

function TreeGen.make(seed: number, giant: boolean?): Tree
	local roll = source(seed)
	local scale = if giant then GIANT_SCALE else 1
	local height = between(roll, 15, 18.5) * scale
	local trunkTop = height * 0.6
	local base = between(roll, 0.95, 1.15) * scale
	local leanX, leanZ = between(roll, -1.6, 1.6) * scale, between(roll, -1.6, 1.6) * scale
	local bendTurn = between(roll, 0, math.pi * 2)
	local bend = between(roll, 0.3, 0.8) * scale

	local limbs: { Limb } = {}
	local lumps: { Lump } = {}
	local masses: { { number } } = {} -- x, y, z, radius of each mass of leaves

	-- The trunk: a few pieces, each thinner than the last, bowing gently to one side.
	local px, py, pz = 0, 0, 0
	for i = 1, SEGMENTS do
		local t = i / SEGMENTS
		local bow = math.sin(t * math.pi) * bend
		local nx = leanX * t + math.cos(bendTurn) * bow
		local nz = leanZ * t + math.sin(bendTurn) * bow
		local ny = trunkTop * t
		local radius = base * (1.3 - 0.8 * ((i - 0.5) / SEGMENTS) ^ 0.7)
		table.insert(
			limbs,
			{ ax = px, ay = py, az = pz, bx = nx, by = ny, bz = nz, r = radius, trunk = true }
		)
		px, py, pz = nx, ny, nz
	end

	-- Branches fork from the top of the trunk, spread evenly around it, each ending in leaves.
	local forks = if roll() < 0.5 then 3 else 4
	local leafRadius = between(roll, 3.4, 4.0) * scale
	local turn = between(roll, 0, math.pi * 2)
	local function mass(x: number, y: number, z: number, radius: number)
		table.insert(masses, { x, y, z, radius })
		for i = 1, 4 do
			local spread = if i == 1 then 0 else radius * 0.5
			local size = radius * (if i == 1 then 1.5 else between(roll, 0.95, 1.25))
			table.insert(lumps, {
				x = x + between(roll, -1, 1) * spread,
				y = y + between(roll, -0.4, 0.6) * spread,
				z = z + between(roll, -1, 1) * spread,
				sx = size,
				sy = size * FLAT,
				sz = size,
				rx = between(roll, -0.45, 0.45),
				ry = between(roll, 0, math.pi),
				rz = between(roll, -0.45, 0.45),
				shade = (i - 1) % 3 + 1,
			})
		end
	end
	for k = 1, forks do
		local angle = turn + math.pi * 2 * (k - 1) / forks + between(roll, -0.4, 0.4)
		local reach = leafRadius * between(roll, 0.95, 1.4)
		local rise = height * between(roll, 0.22, 0.34)
		local mx, mz = px + math.cos(angle) * reach * 0.5, pz + math.sin(angle) * reach * 0.5
		local tx, tz = px + math.cos(angle) * reach, pz + math.sin(angle) * reach
		table.insert(limbs, {
			ax = px,
			ay = py,
			az = pz,
			bx = mx,
			by = py + rise * 0.45,
			bz = mz,
			r = base * 0.4,
			trunk = false,
		})
		table.insert(limbs, {
			ax = mx,
			ay = py + rise * 0.45,
			az = mz,
			bx = tx,
			by = py + rise,
			bz = tz,
			r = base * 0.26,
			trunk = false,
		})
		mass(tx, py + rise + leafRadius * 0.2, tz, leafRadius * between(roll, 0.82, 1.0))
	end
	-- and one mass straight up, so the tree has a top
	table.insert(
		limbs,
		{ ax = px, ay = py, az = pz, bx = px, by = height * 0.92, bz = pz, r = base * 0.3, trunk = false }
	)
	mass(px, height * 0.92 + leafRadius * 0.15, pz, leafRadius * 1.12)

	-- The cells kept: the one the trunk stands in, those the trunk passes through, and those the
	-- leaves fill.
	local cell = TreeGen.CELL
	local cells: { { number } } = { { 0, 0, 0 } }
	local seen: { [string]: boolean } = { ["0,0,0"] = true }
	local reachCells = math.ceil((leafRadius * 2.6 + math.abs(leanX) + math.abs(leanZ)) / cell) + 1
	local topCells = math.ceil((height + leafRadius * 1.5) / cell)
	for cy = 0, topCells do
		for cx = -reachCells, reachCells do
			for cz = -reachCells, reachCells do
				local x, y, z = cx * cell, cy * cell + cell / 2, cz * cell
				local taken = false
				for _, limb in limbs do
					if
						limb.trunk
						and toStretch(x, y, z, limb.ax, limb.ay, limb.az, limb.bx, limb.by, limb.bz)
							< limb.r + cell * 0.45
					then
						taken = true
						break
					end
				end
				if not taken then
					for _, m in masses do
						local dx, dy, dz = x - m[1], (y - m[2]) / FLAT, z - m[3]
						if dx * dx + dy * dy + dz * dz < (m[4] * 0.95) ^ 2 then
							taken = true
							break
						end
					end
				end
				local key = cx .. "," .. cy .. "," .. cz
				if taken and not seen[key] then
					seen[key] = true
					table.insert(cells, { cx, cy, cz })
				end
			end
		end
	end

	return {
		seed = seed,
		giant = giant == true,
		height = height,
		logs = if giant then 48 else 5 + math.floor(roll() * 3),
		hardness = if giant then 60 else 12,
		limbs = limbs,
		lumps = lumps,
		cells = cells,
	}
end

-- Does a sapling become a giant? `roll` is a random number from 0 up to 1.
function TreeGen.isGiant(roll: number): boolean
	return roll < TreeGen.GIANT_CHANCE
end

-- What felling a tree gives besides logs. `roll` is a random number from 0 up to 1.
function TreeGen.saplings(roll: number): number
	return if roll < 0.5 then 2 else 1
end

return TreeGen
