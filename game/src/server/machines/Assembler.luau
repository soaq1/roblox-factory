-- Machines that are told what to make: the assembler, the circuit maker and the manufacturer.
-- The owner picks one craft recipe; from then on the machine takes those ingredients at its
-- inputs and puts the product out, exactly as a processing machine does with its fixed recipes.
-- They only run on electricity (their definitions say so, and Processor enforces it).
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local AssemblyLogic = require(Shared.AssemblyLogic)
local Defs = require(Shared.Defs)
local Recipes = require(Shared.Recipes)
local ItemService = require(script.Parent.Parent.ItemService)
local Kit = require(script.Parent.Parent.MachineKit)
local MachineActs = require(script.Parent.Parent.MachineActs)
local Processor = require(script.Parent.Processor)

local Assembler = {}

-- The recipes each kind of machine can be set to, worked out once.
local choicesFor: { [string]: { number } } = {}
local function choices(id: string): { number }
	local list = choicesFor[id]
	if not list then
		list = AssemblyLogic.choices(id, Recipes.craft, Defs.isItem)
		choicesFor[id] = list
	end
	return list
end

-- Sets what the machine makes; nil sets it to nothing. Anything inside that the new recipe has no
-- use for is put out on top of the machine.
local function choose(machine, index: number?)
	local recipe = index and Recipes.craft[index]
	machine.choice = if recipe then index else nil
	local unwanted = Processor.setRecipes(machine, if recipe then { AssemblyLogic.toProcess(recipe) } else {})
	machine.title = if recipe
		then "만드는 것: " .. Defs.name(recipe.out)
		else "만들 것을 고르세요 (F)"
	local top = machine.center + Vector3.new(0, -1.5 + machine.def.height + 1, 0)
	for id, n in unwanted do
		ItemService.spawnMany(id, n, top)
	end
end

function Assembler.build(machine)
	Processor.build(machine)
	choose(machine, nil)
	Kit.prompt(machine, machine.body, "만들 것 고르기", function(player)
		if player == machine.island.owner then
			MachineActs.show(
				player,
				machine,
				"assembler",
				{ choices = choices(machine.id), current = machine.choice or 0 }
			)
		end
	end)
end

function Assembler.load(machine, saved)
	if type(saved) ~= "table" then
		return
	end
	-- The recipe first: what may stay in the buffer depends on it.
	choose(machine, AssemblyLogic.restore(machine.id, Recipes.craft, Defs.isItem, saved.recipe, saved.makes))
	Processor.load(machine, saved)
end

function Assembler.save(machine)
	local data = Processor.save(machine)
	local recipe = machine.choice and Recipes.craft[machine.choice]
	if recipe then
		data.recipe = machine.choice
		data.makes = recipe.out
	end
	return data
end

-- "recipe" with a position in Recipes.craft sets what to make; with 0 it clears it. Owner only.
function Assembler.act(machine, player: Player, action: string, arg: any)
	if player ~= machine.island.owner or action ~= "recipe" then
		return
	end
	if arg == 0 then
		choose(machine, nil)
	elseif type(arg) == "number" and table.find(choices(machine.id), arg) then
		choose(machine, arg)
	end
end

Assembler.tick = Processor.tick
Assembler.accept = Processor.accept
Assembler.drops = Processor.drops

return Assembler
