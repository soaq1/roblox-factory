--!strict
-- What the farm machines look for around them. The world is asked through small functions, so
-- these rules can be tested without one.
local FarmLogic = {}

export type Cell = { x: number, y: number, z: number }
type Check = (x: number, y: number, z: number) -> boolean

-- The log a logger cuts next: in the nearest trunk within `radius` cells, the highest log, so a
-- tree comes down from the top and nothing is left hanging. `below` and `above` are how many
-- cells under and over the logger's own level it looks.
function FarmLogic.nextLog(
	isLog: Check,
	cx: number,
	cy: number,
	cz: number,
	radius: number,
	below: number,
	above: number
): Cell?
	local best: Cell? = nil
	local bestDistance = math.huge
	for dx = -radius, radius do
		for dz = -radius, radius do
			local distance = dx * dx + dz * dz
			if distance > 0 and distance < bestDistance then
				for y = cy + above, cy - below, -1 do
					if isLog(cx + dx, y, cz + dz) then
						best = { x = cx + dx, y = y, z = cz + dz }
						bestDistance = distance
						break
					end
				end
			end
		end
	end
	return best
end

-- Is there still a log in this trunk, between two heights?
function FarmLogic.trunkStands(isLog: Check, x: number, z: number, yMin: number, yMax: number): boolean
	for y = yMin, yMax do
		if isLog(x, y, z) then
			return true
		end
	end
	return false
end

-- The leaves to clear once the last log of a trunk at (x, y, z) is gone: those around where the
-- tree stood that are not within reach of another trunk.
function FarmLogic.looseLeaves(isLeaf: Check, isLog: Check, x: number, y: number, z: number): { Cell }
	local found: { Cell } = {}
	for dx = -2, 2 do
		for dz = -2, 2 do
			for dy = -1, 6 do
				local lx, ly, lz = x + dx, y + dy, z + dz
				if isLeaf(lx, ly, lz) then
					local held = false
					for ox = -2, 2 do
						for oz = -2, 2 do
							for oy = -4, 1 do
								if isLog(lx + ox, ly + oy, lz + oz) then
									held = true
								end
							end
						end
					end
					if not held then
						table.insert(found, { x = lx, y = ly, z = lz })
					end
				end
			end
		end
	end
	return found
end

-- The nearest cell on the machine's own level that passes `fits`, within `radius` cells. Used for
-- the next empty plot to sow and the next ripe crop to gather. Ties go to the same cell every time.
function FarmLogic.nearest(fits: Check, cx: number, cy: number, cz: number, radius: number): Cell?
	local best: Cell? = nil
	local bestDistance = math.huge
	for dx = -radius, radius do
		for dz = -radius, radius do
			local distance = dx * dx + dz * dz
			if distance > 0 and distance < bestDistance and fits(cx + dx, cy, cz + dz) then
				best = { x = cx + dx, y = cy, z = cz + dz }
				bestDistance = distance
			end
		end
	end
	return best
end

return FarmLogic
