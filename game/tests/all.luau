-- Runs every test file:  lune run tests/all.luau
-- The core tests are in run.luau; each larger system has its own <name>_test.luau.
local fs = require("@lune/fs")
local process = require("@lune/process")

local files = { "tests/run.luau" }
for _, name in fs.readDir("tests") do
	if string.match(name, "_test%.luau$") then
		table.insert(files, "tests/" .. name)
	end
end
table.sort(files)

local failed = false
for _, file in files do
	local result = process.exec("lune", { "run", file })
	print(file .. "  " .. string.gsub(result.stdout, "%s+$", ""))
	if not result.ok then
		failed = true
		if result.stderr ~= "" then
			print(result.stderr)
		end
	end
end
if failed then
	process.exit(1)
end
