-- The card for one thing: how it is made and what it is used in. It opens when the player asks
-- for it (a right click or a long press on a tile, or a press on a picture in the crafting
-- screen) and never by itself. Lines lead on: to the recipe on the crafting screen, or to the
-- card of the machine, the product or the ingredient.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared:WaitForChild("Defs"))
local Recipes = require(Shared:WaitForChild("Recipes"))
local ScreenLogic = require(Shared:WaitForChild("ScreenLogic"))
local CraftUI = require(script.Parent.CraftUI)
local Screens = require(script.Parent.Screens)
local UIKit = require(script.Parent.UIKit)

local InfoCard = {}

local Stock = UIKit.Stock
local LINE = 58
local CHIP = 40
local MAX_CHIPS = 4 -- ingredient pictures shown on one line

local hotbar
local art: Frame
local nameLabel: TextLabel
local kindLabel: TextLabel
local noteLabel: TextLabel
local back: TextButton
local list: ScrollingFrame
local current: string? = nil
local history: { string } = {}
local show: (entry: string, keepHistory: boolean?) -> ()

-- The name of each kind of bench, and the machine that is that bench (for its picture).
local benchNames: { [string]: string } = {}
local benchMachine: { [string]: string } = {}
for id, def in Defs.Machines do
	if def.behavior == "bench" then
		benchNames[def.bench] = def.name
		benchMachine[def.bench] = id
	end
end

local function sortedKeys(bag: { [string]: number }): { string }
	local keys = {}
	for key in bag do
		table.insert(keys, key)
	end
	table.sort(keys, function(a, b)
		return Stock.name(a) < Stock.name(b)
	end)
	return keys
end

-- "철판 2 · 철 막대 2"
local function amounts(bag: { [string]: number }): string
	local parts = {}
	for _, key in sortedKeys(bag) do
		table.insert(parts, Stock.name(key) .. " " .. UIKit.number(bag[key]))
	end
	return table.concat(parts, " · ")
end

-- Where a recipe is carried out, in words, and the thing to picture for it.
local function place(line): (string, string?)
	if line.kind == "craft" then
		if line.bench == "bag" then
			return "가방에서 조합", nil
		end
		local text = (benchNames[line.bench] or line.bench) .. "에서 조합"
		if line.tier > 1 then
			text ..= " · " .. line.tier .. "단계부터"
		end
		return text, benchMachine[line.bench]
	elseif line.kind == "hand" then
		local text = if line.station == "bag"
			then "손으로 (어디서나)"
			else (benchNames[line.station] or line.station) .. "에서 손으로"
		if line.tool then
			text ..= " · 도구: " .. Stock.name(line.tool)
		end
		return text, benchMachine[line.station]
	elseif line.kind == "machine" then
		return Defs.name(line.machine) .. " · " .. line.secs .. "초", line.machine
	elseif line.kind == "extractor" then
		return Defs.name(line.machine) .. "가 내보냄", line.machine
	end
	return (benchNames[line.bench] or tostring(line.bench))
		.. " "
		.. tostring(line.tier)
		.. "단계로 올릴 때",
		benchMachine[line.bench]
end

-- Takes the player to where a recipe can be acted on: the crafting screen for things made by
-- hand, the machine's own card for things a machine makes.
local function follow(line)
	if line.kind == "craft" then
		CraftUI.reveal("craft", line.bench, Stock.name(line.out))
	elseif line.kind == "hand" then
		CraftUI.reveal("hand", line.station, Stock.name(line.out))
	elseif line.kind == "upgrade" then
		CraftUI.reveal("upgrade")
	elseif line.machine then
		show(line.machine, true)
	end
end

local function header(order: number, text: string)
	local label = UIKit.label(list, text, 13)
	label.TextColor3 = UIKit.DIM
	label.TextXAlignment = Enum.TextXAlignment.Left
	label.TextWrapped = false
	label.Size = UDim2.new(1, -10, 0, 22)
	label.LayoutOrder = order
end

-- One recipe as a line: a picture, two lines of text, and for the ways of making the thing, a
-- small picture of each ingredient that opens that ingredient's card.
local function recipeLine(
	order: number,
	line,
	picture: string?,
	top: string,
	bottom: string,
	chips: boolean,
	run: () -> ()
)
	local frame = Instance.new("Frame")
	frame.Size = UDim2.new(1, -10, 0, LINE)
	frame.BackgroundColor3 = UIKit.PANEL
	frame.BorderSizePixel = 0
	frame.LayoutOrder = order
	frame.Parent = list
	UIKit.round(frame, 8)
	UIKit.cover(frame, run)

	local textLeft = 10
	if picture then
		local image = Instance.new("Frame")
		image.BackgroundTransparency = 1
		image.Position = UDim2.fromOffset(6, 6)
		image.Size = UDim2.fromOffset(LINE - 12, LINE - 12)
		image.Parent = frame
		UIKit.picture(image, picture)
		textLeft = LINE
	end

	local keys = if chips then sortedKeys(line.ins) else {}
	local shown = math.min(#keys, MAX_CHIPS)
	local chipsWidth = shown * (CHIP + 4)

	local first = UIKit.label(frame, top, 14)
	first.TextXAlignment = Enum.TextXAlignment.Left
	first.TextWrapped = false
	first.TextTruncate = Enum.TextTruncate.AtEnd
	first.Position = UDim2.fromOffset(textLeft, 8)
	first.Size = UDim2.new(1, -(textLeft + chipsWidth + 12), 0, 20)

	local second = UIKit.label(frame, bottom, 12)
	second.TextColor3 = UIKit.DIM
	second.TextXAlignment = Enum.TextXAlignment.Left
	second.TextWrapped = false
	second.TextTruncate = Enum.TextTruncate.AtEnd
	second.Position = UDim2.fromOffset(textLeft, 30)
	second.Size = UDim2.new(1, -(textLeft + chipsWidth + 12), 0, 18)

	for i = 1, shown do
		local key = keys[i]
		local chip = Instance.new("Frame")
		chip.AnchorPoint = Vector2.new(1, 0.5)
		chip.Position = UDim2.new(1, -8 - (shown - i) * (CHIP + 4), 0.5, 0)
		chip.Size = UDim2.fromOffset(CHIP, CHIP)
		chip.BackgroundColor3 = UIKit.BACK
		chip.BorderSizePixel = 0
		chip.ZIndex = 6 -- above the line's own click cover
		chip.Parent = frame
		UIKit.picture(chip, key) -- first: drawing a picture clears whatever the frame held
		UIKit.round(chip, 6)
		local count = UIKit.label(chip, UIKit.number(line.ins[key]), 11)
		count.AnchorPoint = Vector2.new(1, 1)
		count.Position = UDim2.new(1, -2, 1, 0)
		count.Size = UDim2.fromOffset(CHIP - 4, 12)
		count.TextXAlignment = Enum.TextXAlignment.Right
		count.TextWrapped = false
		count.TextStrokeTransparency = 0.3
		count.ZIndex = 2
		local press = UIKit.cover(chip, function()
			show(key, true)
		end)
		press.ZIndex = 7
	end
end

-- The first thing a recipe makes, by name: what a "used in" line is about.
local function product(line): string?
	return sortedKeys(line.outs)[1]
end

local function draw(entry: string)
	local keys = ScreenLogic.keysOf(Defs, Stock, entry)
	local main = keys[1] or entry
	local info = ScreenLogic.lookup(Defs, Recipes, keys)

	UIKit.picture(art, entry)
	nameLabel.Text = if Stock.isKey(main) then Stock.name(main) else Defs.name(entry)
	local held = 0
	for _, key in keys do
		held += hotbar.bag[key] or 0
	end
	local machine = Defs.Machines[main]
	local item = Defs.Items[main]
	local kind = if machine then "기계 · " .. machine.family elseif item then item.category else "블록"
	if info.fuel then
		kind ..= " · 땔감 (" .. info.fuel .. "번 분)"
	end
	kindLabel.Text = kind .. " · 가진 것 " .. UIKit.number(held)
	noteLabel.Text = if machine then machine.note else ""
	back.Visible = #history > 0

	UIKit.clear(list)
	list.CanvasPosition = Vector2.zero
	local order = 0
	local function nextOrder(): number
		order += 1
		return order
	end

	header(nextOrder(), "만드는 법 " .. #info.made)
	if #info.made == 0 then
		header(nextOrder(), "  만드는 법이 따로 없습니다")
	end
	for _, line in info.made do
		local where, picture = place(line)
		local bottom = if next(line.ins)
			then amounts(line.ins) .. " → " .. amounts(line.outs)
			else amounts(line.outs)
		-- The crafting screen is searched by the name of the product, so carry that along.
		local jump = table.clone(line)
		jump.out = main
		recipeLine(nextOrder(), line, picture or main, where, bottom, true, function()
			follow(jump)
		end)
	end

	header(nextOrder(), "쓰이는 곳 " .. #info.used)
	for _, line in info.used do
		local where = place(line)
		local made = product(line)
		if line.kind == "upgrade" then
			recipeLine(
				nextOrder(),
				line,
				benchMachine[line.bench],
				where,
				amounts(line.ins),
				false,
				function()
					follow(line)
				end
			)
		elseif made then
			local top = Stock.name(made) .. (if line.outs[made] > 1 then " ×" .. line.outs[made] else "")
			recipeLine(nextOrder(), line, made, top, where .. " · " .. amounts(line.ins), false, function()
				show(made, true)
			end)
		end
	end
end

-- Shows the card for a palette entry or a bag key. `keepHistory` is for moving on from one card
-- to another, so that "뒤로" leads back.
show = function(entry: string, keepHistory: boolean?)
	if #ScreenLogic.keysOf(Defs, Stock, entry) == 0 then
		return
	end
	if keepHistory and current and current ~= entry then
		table.insert(history, current)
	elseif not keepHistory then
		history = {}
	end
	current = entry
	Screens.open("info")
	draw(entry)
end

function InfoCard.init(hotbarUi)
	hotbar = hotbarUi
	local compact = UIKit.compact()
	local _, body = UIKit.window(
		"info",
		"자세히",
		if compact then 640 else 600,
		if compact then 300 else 500,
		nil,
		nil,
		function()
			current = nil
			history = {}
		end
	)

	art = Instance.new("Frame")
	art.BackgroundTransparency = 1
	art.Size = UDim2.fromOffset(64, 64)
	art.Parent = body

	nameLabel = UIKit.label(body, "", 17)
	nameLabel.TextXAlignment = Enum.TextXAlignment.Left
	nameLabel.TextWrapped = false
	nameLabel.TextTruncate = Enum.TextTruncate.AtEnd
	nameLabel.Position = UDim2.fromOffset(74, 0)
	nameLabel.Size = UDim2.new(1, -150, 0, 22)

	kindLabel = UIKit.label(body, "", 12)
	kindLabel.TextColor3 = UIKit.DIM
	kindLabel.TextXAlignment = Enum.TextXAlignment.Left
	kindLabel.TextWrapped = false
	kindLabel.TextTruncate = Enum.TextTruncate.AtEnd
	kindLabel.Position = UDim2.fromOffset(74, 24)
	kindLabel.Size = UDim2.new(1, -150, 0, 18)

	noteLabel = UIKit.label(body, "", 12)
	noteLabel.TextXAlignment = Enum.TextXAlignment.Left
	noteLabel.TextWrapped = false
	noteLabel.TextTruncate = Enum.TextTruncate.AtEnd
	noteLabel.Position = UDim2.fromOffset(74, 44)
	noteLabel.Size = UDim2.new(1, -74, 0, 18)

	back = UIKit.button(body, "뒤로", 13)
	back.AnchorPoint = Vector2.new(1, 0)
	back.Position = UDim2.fromScale(1, 0)
	back.Size = UDim2.fromOffset(64, 34)
	back.Visible = false
	back.Activated:Connect(function()
		local last = table.remove(history)
		if last then
			current = last
			draw(last)
		end
	end)

	list = UIKit.scroller(body, nil, 5)
	list.Position = UDim2.fromOffset(0, 72)
	list.Size = UDim2.new(1, 0, 1, -72)

	UIKit.onInfo(function(entry: string)
		show(entry, Screens.isOpen("info"))
	end)
end

return InfoCard
