-- Any machine that turns things into other things: smelter, crusher, press, kiln and the rest.
-- What it accepts and makes comes from the recipe table, so adding a recipe needs no code.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local Defs = require(Shared.Defs)
local ProcessLogic = require(Shared.ProcessLogic)
local Recipes = require(Shared.Recipes)
local Kit = require(script.Parent.Parent.MachineKit)
local ItemService = require(script.Parent.Parent.ItemService)
local Outlet = require(script.Parent.Parent.Outlet)

local Processor = {}

local function describe(machine): string
	local state = machine.state
	local parts = {}
	for id, n in state.buf do
		table.insert(parts, Defs.name(id) .. " " .. n)
	end
	table.sort(parts)
	local text = table.concat(parts, " · ")
	if machine.rules.usesFuel then
		text ..= (if text == "" then "" else "\n") .. "연료 " .. state.fuel
	end
	return text
end

function Processor.build(machine)
	Kit.visual(machine.model, machine.base, machine.id)
	local body = Kit.body(machine)
	local ports = Kit.ports(machine)
	machine.ins = Kit.inputs(ports)
	machine.outs = Kit.outputs(ports)
	machine.nextOut = 1
	machine.rules = {
		recipes = Recipes.byMachine[machine.id] or {},
		usesFuel = Recipes.usesFuel[machine.id] == true,
		fuel = Recipes.fuel,
		cap = Config.MACHINE_BUFFER,
		outCap = Config.MACHINE_OUT,
	}
	machine.state = ProcessLogic.new()
	machine.label = Kit.label(body, machine.def.height)
	machine.shown = ""
end

function Processor.load(machine, saved)
	machine.state = ProcessLogic.sanitize(saved, machine.rules, Defs.isItem)
end

function Processor.save(machine)
	local s = machine.state
	return { buf = table.clone(s.buf), out = table.clone(s.out), fuel = s.fuel }
end

function Processor.tick(machine, dt: number)
	local state, rules = machine.state, machine.rules
	for _, port in machine.ins do
		for _, part in ItemService.inBox(port.box, port.size) do
			local id, count = ItemService.info(part)
			if id then
				local wanted = math.min(count, ProcessLogic.room(state, id, rules))
				if wanted > 0 then
					ProcessLogic.insert(state, id, ItemService.take(part, wanted), rules)
				end
			end
		end
	end

	ProcessLogic.step(state, dt, rules)

	local ready = ProcessLogic.peekOutput(state)
	if ready and #machine.outs > 0 then
		if Outlet.emit(machine, machine.outs[machine.nextOut], ready) then
			ProcessLogic.removeOutput(state, ready)
		end
		machine.nextOut = machine.nextOut % #machine.outs + 1
	end

	local text = describe(machine)
	if text ~= machine.shown then
		machine.shown = text
		machine.label.Text = text
	end
end

-- Called when a neighbouring machine hands an item straight over.
function Processor.accept(machine, id: string, n: number): number
	return ProcessLogic.insert(machine.state, id, n, machine.rules)
end

-- What falls out when the machine is broken.
function Processor.drops(machine): { [string]: number }
	local all = table.clone(machine.state.buf)
	for id, n in machine.state.out do
		all[id] = (all[id] or 0) + n
	end
	return all
end

return Processor
