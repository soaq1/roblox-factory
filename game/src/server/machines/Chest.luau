-- Collects whatever arrives at its back. The owner empties it into their bag.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local Defs = require(Shared.Defs)
local Inventory = require(Shared.Inventory)
local Net = require(Shared.Net)
local Kit = require(script.Parent.Parent.MachineKit)
local ItemService = require(script.Parent.Parent.ItemService)

local Chest = {}
local C = Kit.COLORS
local INTAKE_SIZE = Vector3.new(0.5, 0.9, 2.2)

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
	local model, base = machine.model, machine.base
	Kit.lip(model, base, -1.0, 1.0, Config.BELT_SPEED)
	Kit.part(model, base, Vector3.new(2.0, 2.1, 2.7), Vector3.new(0.5, -0.45, 0), C.wood)
	local lid = Kit.part(model, base, Vector3.new(2.1, 0.4, 2.8), Vector3.new(0.5, 0.8, 0), C.woodDark)
	for _, x in { 0.0, 1.0 } do
		Kit.detail(model, base, Vector3.new(0.25, 2.14, 2.76), Vector3.new(x, -0.45, 0), C.mid)
	end
	Kit.mouth(model, base, -0.5, true)

	local gui = Instance.new("BillboardGui")
	gui.Size = UDim2.fromOffset(170, 80)
	gui.StudsOffset = Vector3.new(0, 1.9, 0)
	gui.MaxDistance = 45
	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.TextColor3 = Color3.new(1, 1, 1)
	label.TextStrokeTransparency = 0.3
	label.Font = Enum.Font.GothamMedium
	label.TextSize = 15
	label.TextYAlignment = Enum.TextYAlignment.Bottom
	label.Parent = gui
	gui.Parent = lid

	local prompt = Instance.new("ProximityPrompt")
	prompt.ActionText = "꺼내기"
	prompt.ObjectText = "상자"
	prompt.KeyboardKeyCode = Enum.KeyCode.F
	prompt.HoldDuration = 0
	prompt.MaxActivationDistance = 10
	prompt.RequiresLineOfSight = false
	prompt.Parent = lid
	prompt.Triggered:Connect(function(player)
		if player ~= machine.island.owner then
			return
		end
		for id, count in machine.state do
			Inventory.add(machine.island.bag, id, count)
		end
		table.clear(machine.state)
		refresh(machine)
		Net.get("Bag"):FireClient(player, machine.island.bag)
	end)

	machine.intakeBox = base * CFrame.new(-0.75, -0.25, 0)
	machine.label = label
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
	for _, part in ItemService.inBox(machine.intakeBox, INTAKE_SIZE) do
		local id, count = ItemService.info(part)
		if id then
			Inventory.add(machine.state, id, ItemService.take(part, count))
			changed = true
		end
	end
	if changed then
		refresh(machine)
	end
end

function Chest.drops(machine): { [string]: number }
	return table.clone(machine.state)
end

return Chest
