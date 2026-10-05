-- Machines that are in the catalogue but do nothing yet. They can be placed and looked at.
local Kit = require(script.Parent.Parent.MachineKit)

local Decor = {}

function Decor.build(machine)
	Kit.visual(machine.model, machine.base, machine.id)
	Kit.body(machine)
end

return Decor
