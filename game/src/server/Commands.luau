-- Chat commands. Each is registered once and reached from both chat systems; when both report the
-- same message it only runs once.
local Players = game:GetService("Players")
local TextChatService = game:GetService("TextChatService")

local Commands = {}

type Handler = (player: Player, args: { string }) -> ()

local handlers: { [string]: Handler } = {}
local last: { [Player]: { text: string, at: number } } = {}

local function run(player: Player, text: string)
	local words = string.split(string.gsub(text, "^%s+", ""), " ")
	local args = {}
	for i = 2, #words do
		if words[i] ~= "" then
			table.insert(args, words[i])
		end
	end
	local handler = handlers[string.lower(words[1] or "")]
	if not handler then
		return
	end
	local now = os.clock()
	local seen = last[player]
	if seen and seen.text == text and now - seen.at < 0.3 then
		return
	end
	last[player] = { text = text, at = now }
	print("chat command from " .. player.Name .. ": " .. text)
	local ok, err = pcall(handler, player, args)
	if not ok then
		warn("command " .. words[1] .. " failed: " .. tostring(err))
	end
end

function Commands.register(alias: string, handler: Handler)
	handlers["/" .. alias] = handler
	local cmd = Instance.new("TextChatCommand")
	cmd.Name = "Cmd" .. alias
	cmd.PrimaryAlias = "/" .. alias
	cmd.Triggered:Connect(function(source, text)
		local player = source and Players:GetPlayerByUserId(source.UserId)
		if player then
			run(player, text)
		end
	end)
	cmd.Parent = TextChatService
end

function Commands.start()
	-- The older chat system does not run TextChatCommands, so listen there as well.
	local function watch(player: Player)
		player.Chatted:Connect(function(message)
			if string.sub(message, 1, 1) == "/" then
				run(player, message)
			end
		end)
	end
	Players.PlayerAdded:Connect(watch)
	for _, player in Players:GetPlayers() do
		watch(player)
	end
	Players.PlayerRemoving:Connect(function(player)
		last[player] = nil
	end)
end

return Commands
