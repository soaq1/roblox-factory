-- Puts out one raw item at a steady pace: ore from a vein core, water from a pump.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Config = require(ReplicatedStorage:WaitForChild("Shared").Config)
local Kit = require(script.Parent.Parent.MachineKit)
local Outlet = require(script.Parent.Parent.Outlet)
local Tuning = require(script.Parent.Parent.Tuning)

local Extractor = {}

function Extractor.build(machine)
	Kit.visual(machine.model, machine.base, machine.id)
	Kit.body(machine)
	machine.out = Kit.outputs(Kit.ports(machine))[1]
	machine.timer = 0
end

function Extractor.tick(machine, dt: number)
	local out = machine.out
	if not out then
		return
	end
	machine.timer = math.min(machine.timer + dt * Tuning.speed, Config.EXTRACT_INTERVAL)
	if machine.timer >= Config.EXTRACT_INTERVAL and Outlet.emit(machine, out, machine.def.item) then
		machine.timer = 0
	end
end

return Extractor
