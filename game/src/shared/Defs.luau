--!strict
-- What exists in the game. Adding a block, item or machine starts with a line here.
local Defs = {}

export type RGB = { number }

Defs.Blocks = {
	grass = { name = "잔디", color = { 109, 189, 88 } },
	dirt = { name = "흙", color = { 154, 106, 68 } },
	stone = { name = "돌", color = { 161, 167, 174 } },
	planks = { name = "판자", color = { 201, 156, 97 } },
	metal = { name = "금속 바닥", color = { 194, 190, 183 } },
	log = { name = "통나무", color = { 138, 100, 62 } },
	leaves = { name = "나뭇잎", color = { 79, 159, 77 } },
} :: { [string]: { name: string, color: RGB } }

Defs.Items = {
	iron_ore = { name = "철 원석", color = { 143, 160, 179 }, size = { 1.0, 0.8, 1.0 } },
	coal = { name = "석탄", color = { 47, 45, 48 }, size = { 0.9, 0.8, 0.9 } },
	iron_ingot = { name = "철 주괴", color = { 205, 211, 219 }, size = { 1.3, 0.5, 0.7 } },
} :: { [string]: { name: string, color: RGB, size: { number } } }

-- `module` names a file in server/machines. Other fields are read by that module.
Defs.Machines = {
	belt = { name = "직선 벨트", module = "Belt", shape = "straight" },
	corner_r = { name = "코너 벨트 (오른쪽)", module = "Belt", shape = "right" },
	corner_l = { name = "코너 벨트 (왼쪽)", module = "Belt", shape = "left" },
	merger = { name = "합류기", module = "Belt", shape = "merge" },
	extractor_iron = {
		name = "추출기 (철)",
		module = "Extractor",
		item = "iron_ore",
		core = { 169, 196, 226 },
	},
	extractor_coal = {
		name = "추출기 (석탄)",
		module = "Extractor",
		item = "coal",
		core = { 75, 70, 84 },
	},
	smelter = { name = "제련로", module = "Smelter" },
	chest = { name = "상자", module = "Chest" },
} :: { [string]: { name: string, module: string, shape: string?, item: string?, core: RGB? } }

-- Order shown in the creative palette.
Defs.Palette = {
	"grass",
	"dirt",
	"stone",
	"planks",
	"metal",
	"log",
	"leaves",
	"belt",
	"corner_r",
	"corner_l",
	"merger",
	"extractor_iron",
	"extractor_coal",
	"smelter",
	"chest",
}

Defs.DefaultHotbar = {
	"grass",
	"stone",
	"metal",
	"belt",
	"corner_r",
	"merger",
	"extractor_iron",
	"extractor_coal",
	"smelter",
}

function Defs.isBlock(id: any): boolean
	return type(id) == "string" and Defs.Blocks[id] ~= nil
end

function Defs.isMachine(id: any): boolean
	return type(id) == "string" and Defs.Machines[id] ~= nil
end

function Defs.isItem(id: any): boolean
	return type(id) == "string" and Defs.Items[id] ~= nil
end

function Defs.isPlaceable(id: any): boolean
	return Defs.isBlock(id) or Defs.isMachine(id)
end

function Defs.name(id: string): string
	local def = Defs.Blocks[id] or Defs.Machines[id] or Defs.Items[id]
	return if def then def.name else id
end

return Defs
