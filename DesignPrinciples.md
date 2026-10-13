# AI-Shell (BAISH?)

The AI shell is a bash wrapper with custom commands and natural language chat integration. It is intended to serve as an alternative to a web UI that allows for more granular control and is embedded in the terminal.

## Design Principles

The AI-Shell is intended to be an extensible, highly customizable, means of incorporating LLMs/Agents into your workflow. The project and features are driven by the following design principles:

* Variable automation: The user should be able to delegate as much or as little as they want to an LLM/Agent.  
* Easier done than said: Sometimes it is more difficult to explicitly define what you want an agent to do than it is to just do it yourself. This architecture allows the user to mix natural language interaction and LLM-powered functions with explicit command execution.  
* Customizable and Extensible: Plugin architecture with extensive configuration and customization options.  
* Embedded in the Workflow: The goal with this shell is to keep the ai capabilities as close to the user’s workflow as possible.. This avoids constantly switching between the terminal and a webui, or offloading too much to the AI. Interacting with AI and non AI components (including chat) should be seamless.  
* Fun: It should be enjoyable to use, build, and extend.

## Features

* Fully functional bash shell: The AI-Shell wraps bash and is intended to work as a bash substitute, allowing the user to perform all of the normal bash operations while also adding additional functionality. All custom components support piping.  
* Natural Language Chat: The shell allows users to chat with an underlying agent directly in the shell via a prefix operator (e.g. ?Why is the sky blue) or by starting an interactive chat session with ‘?”. Optionally the shell can be configured to treat any unresolvable command as a natural language query.  
* Configurable Agents: The shell allows you to configure any number of agents. One agent will be the default for natural language chat, but others can be used by explicitly invoking them.  
* Custom Functions with Dual Purpose: Functions defined using the custom interface can be exposed as tools to any of the agents, used as commands in the shell, or both. This allows for a range of autonomy for different tasks. For example you could have the agent use the built in summarization tool to summarize a large document, or you could directly run something like \`cat large\_document.md | \\summarize\`. This allows for the user to explicitly define and call “AI enabled workflows” rather than rely entirely on the agent correctly parsing and understanding the user input. Sometimes it’s easier to do something than explain what you want.  
* Custom Macros: Similar to functions, macros can be constructed in the shell and can range from simple (like a custom prompt) to more complex (like a pipeline of bash and custom commands).  
* Plugin Architecture: The core of this project is the custom function definition, allowing for dual purpose functions that can be used by an agent or directly invoked by the user. Available functions can be extended via plugins, allowing for extensive customization. Additionally, the front end (by default a custom shell interface that wraps bash) supports plugins, allowing for other front ends such as a different shell, a UI, or an API server.  
* LLM-based parsing: Optional parsers can be used to help coerce the output of one function or command into the input of the next one.  
* Document ingestion capabilities.

Example Use Cases

* Natural language for executing complex bash commands, summarizing or analyzing logs, files, etc.  
* Pipe stdout or stderr into the agent context to allow it to help debug code execution.  
* Create simple commands to automate things like note taking, todo list management, or other menial tasks.  
* Allows the user to manually select AI functions (or MCP tools) and invoke them. Ideally, an AI Parser would allow “python partial-like” behavior, where the user could pin down certain things (like the command and one or two arguments) and then let the agent fill in the other arguments. E.g.,   
  \`\`\`  
  \\parse “Completed the design document and began implementation. Blocked until I get access to the required hardware” | \\jira\_update\_issue NB123  
  \`\`\`  
  This would allow the agent to fill in the other parameters of the command when the user has defined the command and one argument. This is a nice to have.   
* 