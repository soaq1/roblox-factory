-- Workbenches and hand stations. They do nothing by themselves: standing near one is what lets a
-- player craft that kind of thing. A workbench's tier belongs to the island, so every bench of a
-- kind shows the same tier.
local Kit = require(script.Parent.Parent.MachineKit)
local MachineActs = require(script.Parent.Parent.MachineActs)

local Bench = {}

local TIERED =
	{ basic = true, tool = true, part = true, machine = true, cook = true, elec = true, furn = true }

local function text(machine): string
	local kind = machine.def.bench
	if TIERED[kind] then
		return machine.def.name .. " " .. (machine.island.tiers[kind] or 1) .. "단계"
	end
	return machine.def.name
end

function Bench.build(machine)
	Kit.visual(machine.model, machine.base, machine.id)
	local body = Kit.body(machine)
	-- F opens the crafting screen at this bench. Only the owner crafts here.
	Kit.prompt(machine, body, "조합", function(player)
		if player == machine.island.owner then
			MachineActs.show(player, machine, "bench", { bench = machine.def.bench })
		end
	end)
	machine.label = Kit.label(body, machine.def.height)
	machine.shown = text(machine)
	machine.label.Text = machine.shown
end

function Bench.tick(machine, _dt: number)
	local now = text(machine)
	if now ~= machine.shown then
		machine.shown = now
		machine.label.Text = now
	end
end

return Bench
