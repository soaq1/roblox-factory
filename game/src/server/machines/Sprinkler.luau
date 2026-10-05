-- The sprinkler: crops and saplings near it grow faster. It needs nothing fed to it for now.
local DeviceKit = require(script.Parent.Parent.DeviceKit)
local Kit = require(script.Parent.Parent.MachineKit)
local Plant = require(script.Parent.Plant)

local Sprinkler = {}

local RADIUS = 2 -- cells each way, so a 5 by 5 patch
local EVERY = 1 -- seconds between waterings
local LASTS = 2.5 -- seconds one watering keeps a plant wet

function Sprinkler.build(machine)
	Kit.visual(machine.model, machine.base, machine.id)
	Kit.body(machine)
	machine.wait = 0
end

function Sprinkler.tick(machine, dt: number)
	machine.wait -= dt
	if machine.wait > 0 then
		return
	end
	machine.wait = EVERY
	DeviceKit.eachNear(machine, RADIUS, function(other)
		if other.mod == Plant then
			Plant.water(other, LASTS)
		end
	end)
end

return Sprinkler
