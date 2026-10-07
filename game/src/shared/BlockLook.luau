--!strict
-- How a block is drawn. A block whose pictures have been uploaded is a white box wearing a custom
-- material made from its side picture, with its top picture laid on the top face if that differs.
-- Any other block is a box in its side colour, with a thin cap in its top colour when the two
-- differ enough to matter (logs, farmland).
local BlockLook = {}

export type Look = {
	variant: string?, -- the custom material to wear, if the block has pictures
	side: string?, -- the picture that material is made from
	top: string?, -- a picture for the top face alone
	cap: { number }?, -- the colour of a thin cap, for a plain block whose top differs
}

local CAP_DIFFERENCE = 60

-- The name of the custom material a textured block wears.
function BlockLook.variantName(id: string): string
	return "Block_" .. id
end

function BlockLook.of(id: string, def: any): Look
	local tex = def.tex
	if type(tex) == "table" and type(tex.side) == "string" then
		return {
			variant = BlockLook.variantName(id),
			side = tex.side,
			top = if type(tex.top) == "string" then tex.top else nil,
			cap = nil,
		}
	end
	local c, t = def.color, def.top
	local differs = math.abs(t[1] - c[1]) + math.abs(t[2] - c[2]) + math.abs(t[3] - c[3]) > CAP_DIFFERENCE
	return { variant = nil, side = nil, top = nil, cap = if differs then t else nil }
end

-- Every custom material the blocks need: its name and the picture it is made from, in a fixed order.
function BlockLook.variants(blocks: { [string]: any }): { { name: string, image: string } }
	local ids = {}
	for id in blocks do
		table.insert(ids, id)
	end
	table.sort(ids)
	local list = {}
	for _, id in ids do
		local look = BlockLook.of(id, blocks[id])
		if look.variant and look.side then
			table.insert(list, { name = look.variant, image = look.side })
		end
	end
	return list
end

return BlockLook
