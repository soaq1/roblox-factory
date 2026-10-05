-- The storage unit: collects whatever arrives at its input. The owner empties it into their bag.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared.Defs)
local Inventory = require(Shared.Inventory)
local Net = require(Shared.Net)
local Kit = require(script.Parent.Parent.MachineKit)
local ItemService = require(script.Parent.Parent.ItemService)

local Chest = {}

local function refresh(machine)
	local lines = {}
	for id, count in machine.state do
		table.insert(lines, Defs.name(id) .. " " .. count)
	end
	table.sort(lines)
	machine.label.Text = if #lines > 0 then table.concat(lines, "\n") else "비어 있음"
	machine.prompt.Enabled = #lines > 0
end

function Chest.build(machine)
	Kit.visual(machine.model, machine.base, machine.id)
	local body = Kit.body(machine)
	machine.ins = Kit.inputs(Kit.ports(machine))
	machine.label = Kit.label(body, machine.def.height)

	local prompt = Instance.new("ProximityPrompt")
	prompt.ActionText = "꺼내기"
	prompt.ObjectText = machine.def.name
	prompt.KeyboardKeyCode = Enum.KeyCode.F
	prompt.HoldDuration = 0
	prompt.MaxActivationDistance = 10
	prompt.RequiresLineOfSight = false
	prompt.Parent = body
	prompt.Triggered:Connect(function(player)
		if player ~= machine.island.owner then
			return
		end
		for id, count in machine.state do
			Inventory.add(machine.island.bag, id, count)
		end
		table.clear(machine.state)
		refresh(machine)
		Net.get("Bag"):FireClient(player, machine.island.bag) -- only the bag changed
	end)

	machine.prompt = prompt
	machine.state = {}
	refresh(machine)
end

function Chest.load(machine, saved)
	machine.state = Inventory.sanitize(saved, Defs.isItem)
	refresh(machine)
end

function Chest.save(machine)
	return table.clone(machine.state)
end

function Chest.tick(machine, _dt: number)
	local changed = false
	for _, port in machine.ins do
		for _, part in ItemService.inBox(port.box, port.size) do
			local id, count = ItemService.info(part)
			if id then
				Inventory.add(machine.state, id, ItemService.take(part, count))
				changed = true
			end
		end
	end
	if changed then
		refresh(machine)
	end
end

-- Called when a neighbouring machine hands an item straight over.
function Chest.accept(machine, id: string, n: number): number
	Inventory.add(machine.state, id, n)
	refresh(machine)
	return n
end

function Chest.drops(machine): { [string]: number }
	return table.clone(machine.state)
end

return Chest
