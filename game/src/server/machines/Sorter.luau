-- The sorter: the owner names one item. That item leaves by the second mouth (the side); everything
-- else carries straight on through the first. With nothing named, everything carries straight on.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared.Defs)
local Kit = require(script.Parent.Parent.MachineKit)
local MachineActs = require(script.Parent.Parent.MachineActs)
local Passthrough = require(script.Parent.Passthrough)

local Sorter = {}

local function choose(machine, item: string?)
	machine.picked = item
	machine.filter = if item then { [item] = true } else {}
	machine.title = if item
		then "골라내는 것: " .. Defs.name(item)
		else "골라낼 것을 정하세요 (F)"
end

function Sorter.build(machine)
	Passthrough.build(machine)
	machine.sorting = true
	choose(machine, nil)
	Kit.prompt(machine, machine.body, "골라낼 것 정하기", function(player)
		if player == machine.island.owner then
			MachineActs.show(player, machine, "sorter", { current = machine.picked or "" })
		end
	end)
end

function Sorter.load(machine, saved)
	Passthrough.load(machine, saved)
	if type(saved) == "table" and Defs.isItem(saved.picked) then
		choose(machine, saved.picked)
	end
end

function Sorter.save(machine)
	return { held = machine.held, picked = machine.picked }
end

-- "filter" with an item id names the item; with "" it clears it. Owner only.
function Sorter.act(machine, player: Player, action: string, arg: any)
	if player ~= machine.island.owner or action ~= "filter" then
		return
	end
	if arg == "" then
		choose(machine, nil)
	elseif Defs.isItem(arg) then
		choose(machine, arg)
	end
end

Sorter.tick = Passthrough.tick
Sorter.whileHalted = Passthrough.whileHalted
Sorter.accept = Passthrough.accept
Sorter.drops = Passthrough.drops

return Sorter
