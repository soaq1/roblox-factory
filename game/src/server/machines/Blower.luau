-- The blower: a steady push on every loose item in front of it. The push is the same for every
-- item, so light things are sent a long way and heavy things barely shift, or not at all.
-- The push is applied every frame rather than on the machine beat, or items would lurch.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local MoverLogic = require(Shared.MoverLogic)
local DeviceKit = require(script.Parent.Parent.DeviceKit)
local ItemService = require(script.Parent.Parent.ItemService)
local Kit = require(script.Parent.Parent.MachineKit)

local Blower = {}

local CELL = Config.CELL
local RANGE = 3 * CELL -- how far in front of the blower the wind reaches
local FORCE = 36 -- the push, in the engine's units of mass times studs per second squared
local MAX_GAIN = 4 -- most speed one frame's push may add, so a tiny item is not fired like a bullet

local running: { [any]: boolean } = {}
local connected = false

local function blow(machine, dt: number)
	local half = CELL / 2
	local zone = machine.base * CFrame.new(half + RANGE / 2, -0.3, 0)
	local forward = machine.base:VectorToWorldSpace(Vector3.xAxis)
	local mouth = (machine.base * CFrame.new(half, 0, 0)).Position
	for _, part in ItemService.inBox(zone, Vector3.new(RANGE, 2.4, 2.4)) do
		if ItemService.info(part) then
			local distance = (part.Position - mouth):Dot(forward)
			local push = MoverLogic.blow(FORCE, distance, RANGE) * dt
			local mass = part.AssemblyMass
			if push > 0 and mass > 0 then
				part:ApplyImpulse(forward * math.min(push, MAX_GAIN * mass))
			end
		end
	end
end

local function connect()
	if connected then
		return
	end
	connected = true
	RunService.Heartbeat:Connect(function(dt)
		for machine in running do
			-- a signal device can switch a blower off, and it needs electricity
			if not machine.halted and not DeviceKit.unpowered(machine) then
				local ok, err = pcall(blow, machine, math.min(dt, 0.1))
				if not ok then
					warn("blower at " .. machine.key .. " failed: " .. tostring(err))
					running[machine] = nil
				end
			end
		end
	end)
end

function Blower.build(machine)
	Kit.visual(machine.model, machine.base, machine.id)
	local body = Kit.body(machine)
	machine.label = Kit.label(body, machine.def.height)
	machine.shown = ""
	running[machine] = true
	machine.model.Destroying:Connect(function()
		running[machine] = nil
	end)
	connect()
end

function Blower.tick(machine, _dt: number)
	DeviceKit.say(machine, if DeviceKit.unpowered(machine) then DeviceKit.NO_POWER else "")
end

return Blower
