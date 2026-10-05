-- Machines that are told what to make: the assembler, the circuit maker and the manufacturer.
-- The owner picks one craft recipe in the machine's window; from then on the machine takes those
-- ingredients (from its inputs, or by hand through the same window) and puts the product out,
-- exactly as a processing machine does with its fixed recipes.
-- They only run on electricity (their definitions say so, and Processor enforces it).
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local AssemblyLogic = require(Shared.AssemblyLogic)
local Defs = require(Shared.Defs)
local Inventory = require(Shared.Inventory)
local Recipes = require(Shared.Recipes)
local Profile = require(script.Parent.Parent.Profile)
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
-- use for goes back into the owner's bag (it was the owner who changed the recipe).
local function choose(machine, index: number?)
	local recipe = index and Recipes.craft[index]
	machine.choice = if recipe then index else nil
	machine.unset = recipe == nil
	local unwanted = Processor.setRecipes(machine, if recipe then { AssemblyLogic.toProcess(recipe) } else {})
	machine.title = if recipe
		then "만드는 것: " .. Defs.name(recipe.out)
		else "만들 것을 고르세요 (F)"
	if next(unwanted) then
		for id, n in unwanted do
			Inventory.add(machine.island.bag, id, n)
		end
		Profile.push(machine.island)
	end
end

function Assembler.build(machine)
	Processor.build(machine)
	-- The window also carries the list of things this machine can be set to make.
	machine.info = function()
		return { choices = choices(machine.id), current = machine.choice or 0 }
	end
	choose(machine, nil)
	Processor.changed(machine)
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

-- "recipe" with a position in Recipes.craft sets what to make; with 0 it clears it. Everything
-- else is the ordinary machine window (put, take, close). Owner only.
function Assembler.act(machine, player: Player, action: string, arg: any)
	if player ~= machine.island.owner then
		return
	end
	if action ~= "recipe" then
		Processor.act(machine, player, action, arg)
		return
	end
	if arg == 0 then
		choose(machine, nil)
	elseif type(arg) == "number" and table.find(choices(machine.id), arg) then
		choose(machine, arg)
	else
		return
	end
	Processor.changed(machine)
end

Assembler.tick = Processor.tick
Assembler.whileHalted = Processor.whileHalted
Assembler.accept = Processor.accept
Assembler.drops = Processor.drops

return Assembler
