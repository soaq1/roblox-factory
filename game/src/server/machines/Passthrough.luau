-- Machines that move items on without changing them: the splitter, merger, funnel and magnet
-- separator, and (through Sorter) the sorter. Each holds one item at a time. Those whose
-- definition says they need electricity stand still without it.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local Defs = require(Shared.Defs)
local Kit = require(script.Parent.Parent.MachineKit)
local ItemService = require(script.Parent.Parent.ItemService)
local Outlet = require(script.Parent.Parent.Outlet)

local Passthrough = {}

local function describe(machine): string
	local lines = {}
	if machine.title then
		table.insert(lines, machine.title)
	end
	if machine.def.needsPower and not machine.powered then
		table.insert(lines, "전기 없음")
	end
	return table.concat(lines, "\n")
end

function Passthrough.build(machine)
	local def = machine.def
	Kit.visual(machine.model, machine.base, machine.id)
	machine.body = Kit.body(machine)
	local ports = Kit.ports(machine)
	machine.ins = Kit.inputs(ports)
	machine.outs = Kit.outputs(ports)
	machine.nextIn = 1
	machine.nextOut = 1
	machine.held = nil
	if def.topIntake then
		-- A funnel also takes whatever lands in its open top.
		table.insert(machine.ins, {
			kind = "in",
			box = machine.base * CFrame.new(0, -Config.CELL / 2 + def.height + 0.3, 0),
			size = Vector3.new(2.4, 1.0, 2.4),
			spawn = Vector3.zero,
		})
	end
	machine.filter = {}
	for _, id in def.filter or {} do
		machine.filter[id] = true
	end
	-- `sorting` (set by Sorter) sends everything that is not picked out by the first mouth,
	-- instead of taking the mouths in turn.
	machine.sorting = false
	machine.label = Kit.label(machine.body, def.height)
	machine.shown = ""
end

function Passthrough.load(machine, saved)
	if type(saved) == "table" and Defs.isItem(saved.held) then
		machine.held = saved.held
	end
end

function Passthrough.save(machine)
	return { held = machine.held }
end

-- Called when a neighbouring machine hands an item straight over.
function Passthrough.accept(machine, id: string, _n: number): number
	if machine.held then
		return 0
	end
	machine.held = id
	return 1
end

-- Takes one item from the inputs in turn, so one busy input cannot starve the others.
local function pull(machine)
	local count = #machine.ins
	for step = 0, count - 1 do
		local index = (machine.nextIn - 1 + step) % count + 1
		local input = machine.ins[index]
		for _, part in ItemService.inBox(input.box, input.size) do
			local id = ItemService.info(part)
			if id and ItemService.take(part, 1) == 1 then
				machine.held = id
				machine.nextIn = index % count + 1
				return
			end
		end
	end
end

-- With a filter, matching items take the second mouth and the rest the first. Without one, items
-- take the mouths in turn, skipping any that is blocked.
local function push(machine, id: string): boolean
	local outs = machine.outs
	if #outs > 1 and (machine.sorting or next(machine.filter)) then
		return Outlet.emit(machine, if machine.filter[id] then outs[2] else outs[1], id)
	end
	for step = 0, #outs - 1 do
		local index = (machine.nextOut - 1 + step) % #outs + 1
		if Outlet.emit(machine, outs[index], id) then
			machine.nextOut = index % #outs + 1
			return true
		end
	end
	return false
end

function Passthrough.tick(machine, _dt: number)
	local text = describe(machine)
	if text ~= machine.shown then
		machine.shown = text
		machine.label.Text = text
	end
	if #machine.outs == 0 or (machine.def.needsPower and not machine.powered) then
		return
	end
	if not machine.held and #machine.ins > 0 then
		pull(machine)
	end
	if machine.held and push(machine, machine.held) then
		machine.held = nil
	end
end

function Passthrough.drops(machine): { [string]: number }
	return if machine.held then { [machine.held] = 1 } else {}
end

return Passthrough
