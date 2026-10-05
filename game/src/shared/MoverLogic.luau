--!strict
-- Numbers for the devices that move items through the air.
local MoverLogic = {}

-- How fast to throw something, at `angle` above level, for it to come down `distance` away and
-- `rise` higher than it started (negative for lower). Returns nil if that angle cannot reach it.
function MoverLogic.launchSpeed(distance: number, rise: number, gravity: number, angle: number): number?
	local reach = distance * math.tan(angle) - rise
	if distance <= 0 or gravity <= 0 or reach <= 0 then
		return nil
	end
	return math.sqrt(gravity * distance * distance / (2 * math.cos(angle) ^ 2 * reach))
end

-- How hard a blower pushes at a distance from its mouth: full strength for the first part of its
-- range, then fading to nothing at the end of it.
function MoverLogic.blow(force: number, distance: number, range: number): number
	if distance < 0 or distance >= range then
		return 0
	end
	local full = range / 3
	if distance <= full then
		return force
	end
	return force * (range - distance) / (range - full)
end

return MoverLogic
