--!strict
-- Electricity, worked out without any Roblox API so it can be tested.
--
-- Poles join to other poles within `poleLink`. A generator joins a pole that is within the pole's
-- reach, and two generators standing close together join each other. Everything joined this way is
-- one network. A battery or a machine belongs to the network of the nearest pole or generator
-- whose reach it stands in.
--
-- Each beat a network adds up what its generators can give, powers machines in a fixed order
-- (those that cannot run without electricity first), puts what is left into batteries, and takes
-- from batteries when generation falls short. A machine is either powered or not; nothing runs
-- at half strength.
local PowerLogic = {}

export type Device = {
	key: string, -- unique and stable; decides the order machines are served in
	x: number,
	y: number,
	z: number,
	kind: string, -- "pole", "source", "battery" or "load"
	-- source
	supply: number?, -- watts it can give right now
	free: boolean?, -- costs nothing to run (wind, sun), so it is used before fuel is burned
	everywhere: boolean?, -- reaches the whole island with no limit (the endless reactor)
	-- battery
	charge: number?, -- joules held
	capacity: number?,
	rate: number?, -- most watts in or out
	-- load
	demand: number?, -- watts
	need: boolean?, -- cannot run at all without power; served before the rest
	idle: boolean?, -- has nothing to do right now, so it draws nothing
}
export type Settings = { poleLink: number, poleReach: number, sourceReach: number }
export type Net = { supply: number, demand: number, stored: number, capacity: number, endless: boolean }
export type Result = {
	powered: { [string]: boolean }, -- every load
	charge: { [string]: number }, -- every battery, after this beat
	throttle: { [string]: number }, -- every source: the share of its output that was used, 0 to 1
	net: { [string]: Net }, -- every device that is on a network
	links: { { string } }, -- pairs of poles joined by a wire
}

-- How far electricity reaches, in cells (placeholders). The server's power system and the
-- player's reach preview both take their numbers from here, so they cannot disagree.
PowerLogic.REACH_CELLS = {
	poleLink = 10, -- poles this close are joined by a wire
	poleReach = 5, -- a pole feeds machines this close
	sourceReach = 2.5, -- a generator feeds machines this close without any pole
}

-- The same distances in studs, for a grid whose cells are `cell` studs wide.
function PowerLogic.settings(cell: number): Settings
	local reach = PowerLogic.REACH_CELLS
	return {
		poleLink = reach.poleLink * cell,
		poleReach = reach.poleReach * cell,
		sourceReach = reach.sourceReach * cell,
	}
end

export type Spot = { x: number, y: number, z: number, kind: string, everywhere: boolean? }

-- For the reach preview: how far a power machine standing at `spot` feeds the machines around it
-- (0 for one that feeds nothing by itself, such as a battery), and which of the other power
-- machines it would be joined to, by their place in `others`.
--   a pole joins poles within poleLink and generators within its reach
--   a generator joins poles whose reach it stands in, and generators standing close by
function PowerLogic.preview(spot: Spot, others: { Spot }, settings: Settings): (number, { number })
	local joined = {}
	local function close(other: Spot, range: number): boolean
		local dx, dy, dz = spot.x - other.x, spot.y - other.y, spot.z - other.z
		return dx * dx + dy * dy + dz * dz <= range * range
	end
	local reach = 0
	if spot.kind == "pole" then
		reach = settings.poleReach
	elseif spot.kind == "source" and not spot.everywhere then
		reach = settings.sourceReach
	end
	for index, other in others do
		local range = 0
		if spot.kind == "pole" then
			range = if other.kind == "pole"
				then settings.poleLink
				elseif other.kind == "source" then settings.poleReach
				else 0
		elseif spot.kind == "source" then
			range = if other.kind == "pole"
				then settings.poleReach
				elseif other.kind == "source" then settings.sourceReach
				else 0
		end
		if range > 0 and close(other, range) then
			table.insert(joined, index)
		end
	end
	return reach, joined
end

local function near(a: Device, b: Device, range: number): boolean
	local dx, dy, dz = a.x - b.x, a.y - b.y, a.z - b.z
	return dx * dx + dy * dy + dz * dz <= range * range
end

local function distance2(a: Device, b: Device): number
	local dx, dy, dz = a.x - b.x, a.y - b.y, a.z - b.z
	return dx * dx + dy * dy + dz * dz
end

local function sorted(devices: { Device }): { Device }
	local list = table.clone(devices)
	table.sort(list, function(a, b)
		return a.key < b.key
	end)
	return list
end

-- Pairs of poles close enough to be joined by a wire.
function PowerLogic.links(devices: { Device }, settings: Settings): { { string } }
	local poles = {}
	for _, d in sorted(devices) do
		if d.kind == "pole" then
			table.insert(poles, d)
		end
	end
	local links = {}
	for i = 1, #poles do
		for j = i + 1, #poles do
			if near(poles[i], poles[j], settings.poleLink) then
				table.insert(links, { poles[i].key, poles[j].key })
			end
		end
	end
	return links
end

local function totals(list: { Device }): (number, number)
	local stored, capacity = 0, 0
	for _, d in list do
		if d.kind == "battery" then
			stored += d.charge or 0
			capacity += d.capacity or 0
		end
	end
	return stored, capacity
end

-- The order machines are served in: those that need power first, then by key.
local function serveOrder(loads: { Device }): { Device }
	local order = {}
	for _, d in loads do
		if d.need then
			table.insert(order, d)
		end
	end
	for _, d in loads do
		if not d.need then
			table.insert(order, d)
		end
	end
	return order
end

local function activeDemand(loads: { Device }): number
	local total = 0
	for _, d in loads do
		if not d.idle then
			total += d.demand or 0
		end
	end
	return total
end

-- Balances one network for one beat of `dt` seconds.
local function balance(
	sources: { Device },
	batteries: { Device },
	loads: { Device },
	dt: number,
	result: Result
): Net
	local freeSupply, fuelSupply = 0, 0
	for _, s in sources do
		if s.free then
			freeSupply += s.supply or 0
		else
			fuelSupply += s.supply or 0
		end
	end
	local supply = freeSupply + fuelSupply

	-- What each battery could give this beat.
	local canGive: { [string]: number } = {}
	local reserve = 0
	for _, b in batteries do
		local watts = if dt > 0 then math.min(b.rate or 0, (b.charge or 0) / dt) else 0
		canGive[b.key] = watts
		reserve += watts
	end

	local left = supply + reserve
	local used = 0
	for _, load in serveOrder(loads) do
		local demand = load.demand or 0
		if demand <= left + 1e-9 then
			result.powered[load.key] = true
			if not load.idle then
				left -= demand
				used += demand
			end
		end
	end

	local charging = 0 -- watts going into batteries
	if used <= supply then
		local spare = supply - used
		for _, b in batteries do
			local charge, capacity = b.charge or 0, b.capacity or 0
			local room = if dt > 0 then math.max(0, capacity - charge) / dt else 0
			local taken = math.min(spare, b.rate or 0, room)
			result.charge[b.key] = math.min(capacity, charge + taken * dt)
			spare -= taken
			charging += taken
		end
	elseif reserve > 0 then
		-- Every battery gives the same share of what it could.
		local share = math.min(1, (used - supply) / reserve)
		for _, b in batteries do
			result.charge[b.key] = math.max(0, (b.charge or 0) - canGive[b.key] * share * dt)
		end
	end

	-- Fuel is only burned for what wind and sun did not cover.
	local fuelShare = 0
	if fuelSupply > 0 then
		fuelShare = math.clamp((used + charging - freeSupply) / fuelSupply, 0, 1)
	end
	for _, s in sources do
		result.throttle[s.key] = if s.free then 1 else fuelShare
	end

	local stored, capacity = 0, 0
	for _, b in batteries do
		stored += result.charge[b.key]
		capacity += b.capacity or 0
	end
	return {
		supply = supply,
		demand = activeDemand(loads),
		stored = stored,
		capacity = capacity,
		endless = false,
	}
end

function PowerLogic.solve(unsorted: { Device }, settings: Settings, dt: number): Result
	local devices = sorted(unsorted)
	local result: Result = { powered = {}, charge = {}, throttle = {}, net = {}, links = {} }
	result.links = PowerLogic.links(devices, settings)

	local carriers: { Device } = {} -- poles and sources: the things a network is made of
	local endless = false
	for _, d in devices do
		if d.kind == "load" then
			result.powered[d.key] = false
		elseif d.kind == "battery" then
			result.charge[d.key] = d.charge or 0
		elseif d.kind == "source" then
			result.throttle[d.key] = 0
			if d.everywhere and (d.supply or 0) > 0 then
				endless = true
			end
		end
		if d.kind == "pole" or d.kind == "source" then
			table.insert(carriers, d)
		end
	end

	-- An endless source powers the whole island: no poles, no shortage, nothing else needs to burn.
	if endless then
		local loads = {}
		for _, d in devices do
			if d.kind == "load" then
				result.powered[d.key] = true
				table.insert(loads, d)
			elseif d.kind == "battery" then
				local capacity = d.capacity or 0
				result.charge[d.key] = math.min(capacity, (d.charge or 0) + (d.rate or 0) * math.max(dt, 0))
			elseif d.kind == "source" and d.everywhere then
				result.throttle[d.key] = 1
			end
		end
		local _, capacity = totals(devices)
		local stored = 0
		for _, charge in result.charge do
			stored += charge
		end
		local net: Net = {
			supply = math.huge,
			demand = activeDemand(loads),
			stored = stored,
			capacity = capacity,
			endless = true,
		}
		for _, d in devices do
			result.net[d.key] = net
		end
		return result
	end

	-- Join carriers into networks.
	local parent: { number } = {}
	for i = 1, #carriers do
		parent[i] = i
	end
	local function find(i: number): number
		while parent[i] ~= i do
			parent[i] = parent[parent[i]]
			i = parent[i]
		end
		return i
	end
	for i = 1, #carriers do
		for j = i + 1, #carriers do
			local a, b = carriers[i], carriers[j]
			local range
			if a.kind == "pole" and b.kind == "pole" then
				range = settings.poleLink
			elseif a.kind == "pole" or b.kind == "pole" then
				range = settings.poleReach
			else
				range = settings.sourceReach
			end
			if near(a, b, range) then
				parent[find(i)] = find(j)
			end
		end
	end

	type Group = { sources: { Device }, batteries: { Device }, loads: { Device }, members: { Device } }
	local groups: { [number]: Group } = {}
	local function groupOf(index: number): Group
		local root = find(index)
		local group = groups[root]
		if not group then
			group = { sources = {}, batteries = {}, loads = {}, members = {} }
			groups[root] = group
		end
		return group
	end
	for i, carrier in carriers do
		local group = groupOf(i)
		table.insert(group.members, carrier)
		if carrier.kind == "source" then
			table.insert(group.sources, carrier)
		end
	end

	-- Batteries and machines go to the nearest carrier whose reach they stand in.
	for _, d in devices do
		if d.kind == "battery" or d.kind == "load" then
			local best: number? = nil
			local bestDistance = math.huge
			for i, carrier in carriers do
				local reach = if carrier.kind == "pole" then settings.poleReach else settings.sourceReach
				local apart = distance2(d, carrier)
				if apart <= reach * reach and apart < bestDistance then
					best, bestDistance = i, apart
				end
			end
			if best then
				local group = groupOf(best)
				table.insert(group.members, d)
				table.insert(if d.kind == "battery" then group.batteries else group.loads, d)
			end
		end
	end

	for _, group in groups do
		local net = balance(group.sources, group.batteries, group.loads, dt, result)
		for _, d in group.members do
			result.net[d.key] = net
		end
	end
	return result
end

-- How hard the wind blows, from 0 to 1, at time `t` seconds. `seed` shifts it so different
-- islands do not rise and fall together. Slow swells with gusts on top; sometimes it drops to nothing.
function PowerLogic.wind(t: number, seed: number): number
	local swell = math.sin(t / 47 + seed * 1.7)
	local breeze = math.sin(t / 13.1 + seed * 3.1)
	local gust = math.sin(t / 3.7 + seed * 5.3)
	return math.clamp(0.45 + 0.4 * swell + 0.2 * breeze + 0.1 * gust, 0, 1)
end

-- How much sun a panel gets, from 0 to 1: nothing at night, most at noon, less when cloud passes.
-- `clock` is the hour of the day from 0 to 24.
function PowerLogic.solar(clock: number, t: number): number
	local sun = math.max(0, math.sin((clock - 6) / 12 * math.pi))
	local cloud = 0.8 + 0.2 * math.sin(t / 53)
	return math.clamp(sun * cloud, 0, 1)
end

return PowerLogic
