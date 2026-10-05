-- The pusher: items pass straight through it, but while a signal reaches it they are pushed out
-- of its side mouth instead. Put a sensor, switch, timer or logic box against it to drive it.
-- (See shared/SignalLogic: `machine.signalled` is set by the signal devices touching a machine.)
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Defs = require(ReplicatedStorage:WaitForChild("Shared").Defs)
local DeviceKit = require(script.Parent.Parent.DeviceKit)
local Kit = require(script.Parent.Parent.MachineKit)
local Outlet = require(script.Parent.Parent.Outlet)

local Pusher = {}

function Pusher.build(machine)
	Kit.visual(machine.model, machine.base, machine.id)
	local body = Kit.body(machine)
	local ports = Kit.ports(machine)
	machine.ins = Kit.inputs(ports)
	local outs = Kit.outputs(ports)
	machine.ahead, machine.aside = outs[1], outs[2] or outs[1]
	machine.held = nil
	machine.label = Kit.label(body, machine.def.height)
	machine.shown = ""
end

function Pusher.load(machine, saved)
	if type(saved) == "table" and Defs.isItem(saved.held) then
		machine.held = saved.held
	end
end

function Pusher.save(machine)
	return { held = machine.held }
end

function Pusher.accept(machine, id: string, _n: number): number
	if machine.held then
		return 0
	end
	machine.held = id
	return 1
end

function Pusher.tick(machine, _dt: number)
	if not machine.ahead then
		return
	end
	machine.busy = machine.held ~= nil -- an empty pusher draws no power
	if DeviceKit.unpowered(machine) then
		DeviceKit.say(machine, DeviceKit.NO_POWER)
		return
	end
	if not machine.held then
		machine.held = DeviceKit.pull(machine)
	end
	local pushing = machine.signalled == true
	if
		machine.held and Outlet.emit(machine, if pushing then machine.aside else machine.ahead, machine.held)
	then
		machine.held = nil
	end
	DeviceKit.say(machine, if pushing then "옆으로 미는 중" else "그대로 통과")
end

function Pusher.drops(machine): { [string]: number }
	return if machine.held then { [machine.held] = 1 } else {}
end

return Pusher
