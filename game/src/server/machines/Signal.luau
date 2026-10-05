-- Signal devices: switch, sensor, timer, counter, logic box, gate and beacon. The rule for who is
-- on is in shared/SignalLogic; read the top of that file first. This module gives each device its
-- shape and its prompt, feeds the rule what each source sees, and carries out the result: gates
-- open and shut, beacons light, and the ordinary machines touching the devices are started,
-- stopped and signalled.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared.Defs)
local SignalLogic = require(Shared.SignalLogic)
local DeviceKit = require(script.Parent.Parent.DeviceKit)
local ItemService = require(script.Parent.Parent.ItemService)
local Kit = require(script.Parent.Parent.MachineKit)

local Signal = {}

local SWEEP_SECONDS = 0.1 -- at least this long between two workings-out of one island's signals
local ON_BELT = { sensor = true, gate = true, counter = true } -- built as a stretch of belt
local MODE_NAMES =
	{ ["and"] = "모두 켜지면", ["or"] = "하나라도 켜지면", ["not"] = "모두 꺼지면" }
local PROMPTS = {
	switch = "켜고 끄기",
	timer = "간격 바꾸기",
	logic = "조건 바꾸기",
	gate = "평소 상태 바꾸기",
	counter = "목표 수 바꾸기",
	sensor = "조건 걸기",
}
-- Where each device's light sits, in its own frame.
local LAMPS = {
	switch = { at = Vector3.new(0, 0.47, -0.34), size = Vector3.new(0.42, 0.42, 0.42), round = true },
	timer = { at = Vector3.new(0, 0.42, 0), size = Vector3.new(0.4, 0.2, 0.4) },
	logic = { at = Vector3.new(0.7, -0.33, 0.45), size = Vector3.new(0.3, 0.14, 0.3) },
	gate = { at = Vector3.new(0, 1.5, 0), size = Vector3.new(0.3, 0.46, 0.7) },
	counter = { at = Vector3.new(0, 1.42, 1.59), size = Vector3.new(0.5, 0.18, 0.3) },
	sensor = { at = Vector3.new(0, 1.77, -1.56), size = Vector3.new(0.36, 0.36, 0.36), round = true },
	beacon = { at = Vector3.new(0, 2.49, 0), size = Vector3.new(0.84, 0.5, 0.84) },
}

local function onOff(on: boolean): string
	return if on then "켜짐" else "꺼짐"
end

local function describe(machine): string
	local kind, s = machine.def.signal, machine.state
	if DeviceKit.unpowered(machine) then
		return DeviceKit.NO_POWER
	elseif kind == "switch" then
		return onOff(machine.on)
	elseif kind == "timer" then
		return s.period .. "초마다 · " .. onOff(machine.on)
	elseif kind == "logic" then
		return MODE_NAMES[s.mode] .. " · " .. onOff(machine.on)
	elseif kind == "gate" then
		return (if machine.on then "열림" else "닫힘") .. (if s.invert then " · 평소 열림" else "")
	elseif kind == "counter" then
		return s.count .. " / " .. s.target
	elseif kind == "sensor" then
		return (if s.filter then Defs.name(s.filter) else "모든 아이템") .. " · " .. onOff(machine.on)
	end
	return ""
end

-- Shows the device's state: its light, its read-out and, for a gate, its barrier.
local function show(machine)
	DeviceKit.setLamp(machine.lamp, machine.on)
	if machine.glow then
		machine.glow.Enabled = machine.on
	end
	if machine.barrier then
		-- `on` means open: the barrier lets items through and fades out of the way
		machine.barrier.CanCollide = not machine.on
		machine.barrier.Transparency = if machine.on then 0.85 else 0
	end
	DeviceKit.say(machine, describe(machine))
end

-- The items a sensor or counter is looking at right now.
local function watched(machine): { BasePart }
	local found = {}
	local filter = machine.state.filter
	for _, part in DeviceKit.onBed(machine) do
		local id = ItemService.info(part)
		if id and (not filter or id == filter) then
			table.insert(found, part)
		end
	end
	return found
end

-- How many items have arrived on a counter since the last look. A stack counts as all it holds.
local function arrivals(machine): number
	local now, passed = {}, 0
	for _, part in watched(machine) do
		local uid = part:GetAttribute("Uid")
		local _, count = ItemService.info(part)
		if uid then
			now[uid] = true
			if not machine.seen[uid] then
				passed += count
			end
		end
	end
	machine.seen = now
	return passed
end

type Net = { devices: { [any]: boolean }, affected: { [any]: boolean }, last: number }

local function netOf(island): Net
	local net = island.extra.signal
	if not net then
		net = { devices = {}, affected = {}, last = 0 }
		island.extra.signal = net
	end
	return net
end

local function release(net: Net)
	for other in net.affected do
		other.signalled = nil
		other.halted = nil
	end
	net.affected = {}
end

-- Works out every signal device on the island at once, then tells the ordinary machines touching
-- them whether they are signalled and whether they may run.
local function sweep(island)
	local net = netOf(island)
	local list, index = {}, {}
	for device in net.devices do
		table.insert(list, device)
		index[device] = #list
	end
	local nodes, near = {}, {}
	for i, device in list do
		local links, others = {}, {}
		for _, other in DeviceKit.touching(device) do
			if index[other] then
				table.insert(links, index[other])
			else
				table.insert(others, other)
			end
		end
		near[i] = others
		nodes[i] = {
			kind = device.def.signal,
			on = device.on,
			raw = device.raw,
			mode = device.state.mode,
			invert = device.state.invert,
			dead = DeviceKit.unpowered(device),
			links = links,
		}
	end
	for i, on in SignalLogic.step(nodes) do
		list[i].on = on
		show(list[i])
	end

	-- For each ordinary machine: the senders touching it, and the controllers among them.
	local told: { [any]: { senders: { boolean }, controllers: { boolean } } } = {}
	for i, device in list do
		local kind = device.def.signal
		if SignalLogic.isSender(kind) then
			for _, other in near[i] do
				local entry = told[other]
				if not entry then
					entry = { senders = {}, controllers = {} }
					told[other] = entry
				end
				table.insert(entry.senders, device.on)
				if SignalLogic.isController(kind) then
					table.insert(entry.controllers, device.on)
				end
			end
		end
	end
	local affected = {}
	for other, entry in told do
		local signalled, halted = SignalLogic.forMachine(entry.senders, entry.controllers)
		other.signalled = signalled
		-- A pusher is steered by its signal, not stopped by it.
		other.halted = halted and other.def.behavior ~= "pusher"
		affected[other] = true
	end
	for other in net.affected do
		if not affected[other] then
			other.signalled = nil
			other.halted = nil
		end
	end
	net.affected = affected
end

-- What the owner's prompt does to each kind of device.
local function use(machine)
	local kind, s = machine.def.signal, machine.state
	if kind == "switch" then
		s.on = not s.on
	elseif kind == "timer" then
		s.period = SignalLogic.nextOf(SignalLogic.PERIODS, s.period)
		s.t = 0
	elseif kind == "logic" then
		s.mode = SignalLogic.nextOf(SignalLogic.MODES, s.mode)
	elseif kind == "gate" then
		s.invert = not s.invert
	elseif kind == "counter" then
		s.target = SignalLogic.nextOf(SignalLogic.TARGETS, s.target)
		s.count = 0
	elseif kind == "sensor" then
		-- Watches for whatever is on it when the prompt is pressed; pressed when empty, it goes
		-- back to watching for everything.
		local part = DeviceKit.onBed(machine)[1]
		s.filter = if part then ItemService.info(part) else nil
	end
	show(machine)
end

function Signal.act(machine, player: Player, action: string, _arg: any)
	if action == "use" and DeviceKit.isOwner(machine, player) and PROMPTS[machine.def.signal] then
		use(machine)
	end
end

function Signal.build(machine)
	local kind = machine.def.signal
	local visual = Kit.visual(machine.model, machine.base, machine.id)
	local anchor: BasePart
	if ON_BELT[kind] then
		anchor = DeviceKit.bed(machine)
	else
		anchor = Kit.body(machine)
	end

	if kind == "gate" then
		-- The model shows its barrier half raised. It is replaced by one that really moves.
		if visual then
			for _, part in visual:GetChildren() do
				if part:IsA("BasePart") and math.abs(part.Size.Y - 3.06 / 3) < 0.02 then
					part:Destroy()
				end
			end
		end
		machine.barrier = Kit.part(
			machine.model,
			machine.base,
			Vector3.new(0.2, 1.25, 2.3),
			Vector3.new(0, DeviceKit.BELT_TOP + 0.62, 0),
			Color3.fromRGB(217, 72, 59)
		)
	end

	local lamp = LAMPS[kind]
	machine.lamp = DeviceKit.lamp(machine, lamp.at, lamp.size, lamp.round)
	if kind == "beacon" then
		local glow = Instance.new("PointLight")
		glow.Color = Color3.fromRGB(120, 220, 140)
		glow.Range = 16
		glow.Brightness = 2
		glow.Enabled = false
		glow.Parent = machine.lamp
		machine.glow = glow
	else
		machine.label = Kit.label(anchor, 3)
	end
	if PROMPTS[kind] then
		Kit.prompt(machine, anchor, PROMPTS[kind], function(player)
			Signal.act(machine, player, "use", nil)
		end)
	end

	machine.state = SignalLogic.sanitize(kind, nil, Defs.isItem)
	machine.on = false
	machine.raw = false
	machine.pulse = 0
	machine.seen = {}
	machine.shown = ""
	show(machine)

	local island = machine.island
	local net = netOf(island)
	net.devices[machine] = true
	machine.model.Destroying:Connect(function()
		net.devices[machine] = nil
		-- With no device left nothing will work the signals out again, so let go of every
		-- machine now. Otherwise the next sweep does it.
		if next(net.devices) == nil then
			release(net)
		end
	end)
end

function Signal.load(machine, saved)
	machine.state = SignalLogic.sanitize(machine.def.signal, saved, Defs.isItem)
	show(machine)
end

function Signal.save(machine)
	return table.clone(machine.state)
end

function Signal.tick(machine, dt: number)
	local kind, s = machine.def.signal, machine.state
	if DeviceKit.unpowered(machine) then
		-- No electricity: it sees and counts nothing. The sweep treats it as off.
		machine.raw = false
		machine.seen = {}
	elseif kind == "switch" then
		machine.raw = s.on
	elseif kind == "sensor" then
		machine.raw = #watched(machine) > 0
	elseif kind == "timer" then
		s.t = (s.t + dt) % s.period
		machine.raw = SignalLogic.timerOn(s.t, s.period)
	elseif kind == "counter" then
		machine.pulse = math.max(0, machine.pulse - dt)
		local count, fired = SignalLogic.count(s.count, s.target, arrivals(machine))
		s.count = count
		if fired then
			machine.pulse = SignalLogic.PULSE
		end
		machine.raw = machine.pulse > 0
	end

	local net = netOf(machine.island)
	local now = os.clock()
	if now - net.last >= SWEEP_SECONDS then
		net.last = now
		sweep(machine.island)
	end
	show(machine)
end

return Signal
