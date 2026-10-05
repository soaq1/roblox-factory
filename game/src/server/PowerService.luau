-- Runs the electricity on every island. Once a beat it gathers each island's power machines and
-- the machines that use power, lets shared/PowerLogic work out the networks and who gets what,
-- writes the answers back onto the machines, and keeps the wires between poles drawn.
--
-- What it reads from a machine:  supply, free, everywhere (generators); charge, capacity, rate
--                                (batteries); busy (false when a machine has nothing to do).
-- What it writes to a machine:   powered (anything that uses power), throttle (generators),
--                                charge (batteries), net (everything on a network).
-- Any machine whose definition says needsPower is counted; its own module decides what being
-- unpowered means by reading `machine.powered`.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local PowerLogic = require(Shared.PowerLogic)
local IslandService = require(script.Parent.IslandService)
local MachineService = require(script.Parent.MachineService)

local PowerService = {}

-- All placeholder numbers.
PowerService.BEAT = 1 -- seconds between rounds
PowerService.SETTINGS = {
	poleLink = 10 * Config.CELL, -- poles this close are joined by a wire
	poleReach = 5 * Config.CELL, -- a pole feeds machines this close
	sourceReach = 2.5 * Config.CELL, -- a generator feeds machines this close without any pole
}
PowerService.NEED_WATTS = 20 -- per cell of floor, for machines that cannot run without power
PowerService.BOOST_WATTS = 10 -- per cell of floor, for ordinary machines that are sped up by it

local WIRE_COLOR = Color3.fromRGB(43, 42, 41)

local function deviceFor(machine): PowerLogic.Device?
	local def = machine.def
	local device: any
	if def.behavior == "power" then
		if def.power == "pole" then
			device = { kind = "pole" }
		elseif def.power == "battery" then
			device = {
				kind = "battery",
				charge = machine.charge or 0,
				capacity = machine.capacity,
				rate = machine.rate,
			}
		else
			device = {
				kind = "source",
				supply = machine.supply or 0,
				free = machine.free == true,
				everywhere = machine.everywhere == true,
			}
		end
	elseif def.needsPower then
		device = { kind = "load", demand = PowerService.NEED_WATTS * def.sx * def.sz, need = true }
	elseif def.behavior == "processor" then
		device = { kind = "load", demand = PowerService.BOOST_WATTS * def.sx * def.sz, need = false }
	else
		return nil
	end
	device.idle = machine.busy == false
	device.key = machine.key
	device.x, device.y, device.z = machine.center.X, machine.center.Y, machine.center.Z
	return device
end

-- Where a wire is tied to a pole: just under its top.
local function wireEnd(machine): Vector3
	return machine.center + Vector3.new(0, -Config.CELL / 2 + machine.def.height - 0.5, 0)
end

-- Makes the wires on an island match the links between its poles.
local function drawWires(island, links: { { string } }, byKey)
	local store = island.extra.power
	if not store then
		local folder = Instance.new("Folder")
		folder.Name = "Wires"
		folder.Parent = island.folder
		store = { folder = folder, wires = {} }
		island.extra.power = store
	end
	local wanted: { [string]: boolean } = {}
	for _, link in links do
		local name = link[1] .. "|" .. link[2]
		wanted[name] = true
		if not store.wires[name] then
			local from, to = wireEnd(byKey[link[1]]), wireEnd(byKey[link[2]])
			local length = (to - from).Magnitude
			if length > 0.01 then
				local wire = Instance.new("Part")
				wire.Name = "Wire"
				wire.Anchored = true
				wire.CanCollide = false
				wire.CanQuery = false
				wire.CanTouch = false
				wire.CastShadow = false
				wire.Material = Enum.Material.SmoothPlastic
				wire.Color = WIRE_COLOR
				wire.Size = Vector3.new(0.12, 0.12, length)
				wire.CFrame = CFrame.lookAt((from + to) / 2, to)
				wire.Parent = store.folder
				store.wires[name] = wire
			end
		end
	end
	for name, wire in store.wires do
		if not wanted[name] then
			wire:Destroy()
			store.wires[name] = nil
		end
	end
end

local function step(island, dt: number)
	local devices: { PowerLogic.Device } = {}
	local byKey = {}
	for _, machine in MachineService.onIsland(island) do
		local device = deviceFor(machine)
		if device then
			table.insert(devices, device)
			byKey[machine.key] = machine
		end
	end
	local result = PowerLogic.solve(devices, PowerService.SETTINGS, dt)
	for _, device in devices do
		local machine = byKey[device.key]
		if device.kind == "load" then
			machine.powered = result.powered[device.key] == true
		elseif device.kind == "battery" then
			machine.charge = result.charge[device.key]
		elseif device.kind == "source" then
			machine.throttle = result.throttle[device.key]
		end
		machine.net = result.net[device.key]
	end
	-- Nothing to draw and nothing drawn: leave the island alone.
	if #result.links > 0 or island.extra.power then
		drawWires(island, result.links, byKey)
	end
end

function PowerService.start()
	task.spawn(function()
		local last = os.clock()
		while true do
			task.wait(PowerService.BEAT)
			local now = os.clock()
			-- After a long stall, run one beat rather than paying out for all the lost time at once.
			local dt = math.min(now - last, PowerService.BEAT * 3)
			last = now
			for _, island in IslandService.all() do
				local ok, err = pcall(step, island, dt)
				if not ok then
					warn("power on island " .. island.slot .. " failed: " .. tostring(err))
				end
			end
		end
	end)
end

return PowerService
