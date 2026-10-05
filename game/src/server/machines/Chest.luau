-- Storage: the storage unit collects whatever a belt brings to its input, and the hand chest
-- whatever is dropped onto its lid. F opens it like a chest in Minecraft: the owner's bag on one
-- side and the chest on the other, and a click moves a thing across. A chest holds anything a bag
-- can: items, machines and blocks.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared.Defs)
local Inventory = require(Shared.Inventory)
local StoreLogic = require(Shared.StoreLogic)
local DeviceKit = require(script.Parent.Parent.DeviceKit)
local Kit = require(script.Parent.Parent.MachineKit)
local ItemService = require(script.Parent.Parent.ItemService)
local Profile = require(script.Parent.Parent.Profile)
local Watch = require(script.Parent.Parent.Watch)

local Chest = {}

local Stock = Profile.Stock
local LABEL_LINES = 5 -- kinds listed on the label before it says "and so many more"

local function refresh(machine)
	local lines = {}
	for key, count in machine.state do
		table.insert(lines, Stock.name(key) .. " " .. count)
	end
	table.sort(lines)
	if #lines == 0 then
		machine.label.Text = "비어 있음"
	elseif #lines > LABEL_LINES then
		local shown = table.move(lines, 1, LABEL_LINES, 1, {})
		machine.label.Text = table.concat(shown, "\n") .. "\n외 " .. (#lines - LABEL_LINES) .. "종"
	else
		machine.label.Text = table.concat(lines, "\n")
	end
end

local function snapshot(machine): { [string]: any }
	return { contents = table.clone(machine.state) }
end

-- Brings the label and any open window up to date.
local function changed(machine, force: boolean?)
	refresh(machine)
	Watch.push(machine, function()
		return snapshot(machine)
	end, force)
end

function Chest.build(machine)
	Kit.visual(machine.model, machine.base, machine.id)
	local body = Kit.body(machine)
	machine.ins = Kit.inputs(Kit.ports(machine))
	if machine.def.topIntake then
		table.insert(machine.ins, DeviceKit.top(machine))
	end
	machine.label = Kit.label(body, machine.def.height)
	local gui = machine.label.Parent
	if gui and gui:IsA("BillboardGui") then
		gui.Size = UDim2.fromOffset(190, 110)
	end
	machine.state = {}
	machine.prompt = Kit.prompt(machine, body, "열기", function(player)
		if player == machine.island.owner then
			Watch.open(machine, player, "chest", snapshot(machine))
		end
	end)
	refresh(machine)
end

function Chest.load(machine, saved)
	machine.state = Inventory.sanitize(saved, Stock.isKey)
	refresh(machine)
end

function Chest.save(machine)
	return table.clone(machine.state)
end

function Chest.tick(machine, _dt: number)
	local taken = false
	for _, port in machine.ins do
		for _, part in ItemService.inBox(port.box, port.size) do
			local id, count = ItemService.info(part)
			if id then
				Inventory.add(machine.state, id, ItemService.take(part, count))
				taken = true
			end
		end
	end
	if taken then
		changed(machine)
	end
end

-- What the owner does in the chest's window:
--   "put"   { key, n }  from the bag into the chest
--   "take"  { key, n }  from the chest into the bag
--   "takeall"           everything in the chest into the bag
--   "close"             the window was closed
function Chest.act(machine, player: Player, action: string, arg: any)
	if player ~= machine.island.owner then
		return
	end
	if action == "close" then
		Watch.close(machine, player)
		return
	end
	local bag = machine.island.bag
	local moved = 0
	if action == "takeall" then
		moved = StoreLogic.moveAll(machine.state, bag)
	elseif type(arg) ~= "table" or not Stock.isKey(arg.key) then
		return
	elseif action == "put" then
		moved = StoreLogic.move(bag, machine.state, arg.key, arg.n)
	elseif action == "take" then
		moved = StoreLogic.move(machine.state, bag, arg.key, arg.n)
	else
		return
	end
	if moved > 0 then
		Profile.push(machine.island)
	end
	changed(machine, true)
end

-- Called when a neighbouring machine hands an item straight over.
function Chest.accept(machine, id: string, n: number): number
	Inventory.add(machine.state, id, n)
	changed(machine)
	return n
end

-- What falls out when the chest is broken. Loose items can only be items, so any machines and
-- blocks kept inside go straight back into the owner's bag instead of being lost.
function Chest.drops(machine): { [string]: number }
	local loose = {}
	local kept = false
	for key, count in machine.state do
		if not Defs.isItem(key) then
			Inventory.add(machine.island.bag, key, count)
			kept = true
		else
			loose[key] = count
		end
	end
	table.clear(machine.state)
	if kept then
		Profile.push(machine.island)
	end
	return loose
end

return Chest
