--!strict
-- Which craft recipes a machine that is told what to make can be set to, and how such a recipe
-- looks to the processing rules. Everything that goes in or comes out travels as loose items on
-- belts, so only recipes made wholly of items qualify.
local AssemblyLogic = {}

export type Craft = { out: string, n: number, bench: string, tier: number, ins: { [string]: number } }
export type Process = { ins: { [string]: number }, outs: { [string]: number }, secs: number }

AssemblyLogic.SECONDS = 4 -- how long one assembly takes (a placeholder)

-- The three machines differ in what they can be set to:
--   circuit       things made at the electrics workbench, from one or two kinds of ingredient
--   assembler     anything else made from one or two kinds of ingredient
--   manufacturer  anything at all
function AssemblyLogic.allowed(machineId: string, recipe: Craft, isItem: (string) -> boolean): boolean
	if not isItem(recipe.out) then
		return false
	end
	local kinds = 0
	for key in recipe.ins do
		if not isItem(key) then
			return false
		end
		kinds += 1
	end
	if kinds == 0 then
		return false
	end
	if machineId == "manufacturer" then
		return true
	end
	if kinds > 2 then
		return false
	end
	if machineId == "circuit" then
		return recipe.bench == "elec"
	end
	return recipe.bench ~= "elec"
end

-- The positions in `craft` of every recipe this machine can be set to.
function AssemblyLogic.choices(machineId: string, craft: { Craft }, isItem: (string) -> boolean): { number }
	local list = {}
	for index, recipe in craft do
		if AssemblyLogic.allowed(machineId, recipe, isItem) then
			table.insert(list, index)
		end
	end
	return list
end

function AssemblyLogic.toProcess(recipe: Craft): Process
	return { ins = table.clone(recipe.ins), outs = { [recipe.out] = recipe.n }, secs = AssemblyLogic.SECONDS }
end

-- Finds a stored choice again. Recipes can be reordered between versions, so the product's name
-- is trusted over the position: the position is used only if it still makes the same thing.
function AssemblyLogic.restore(
	machineId: string,
	craft: { Craft },
	isItem: (string) -> boolean,
	index: any,
	out: any
): number?
	if type(out) ~= "string" then
		return nil
	end
	if type(index) == "number" and index % 1 == 0 and craft[index] then
		local recipe = craft[index]
		if recipe.out == out and AssemblyLogic.allowed(machineId, recipe, isItem) then
			return index
		end
	end
	for i, recipe in craft do
		if recipe.out == out and AssemblyLogic.allowed(machineId, recipe, isItem) then
			return i
		end
	end
	return nil
end

return AssemblyLogic
