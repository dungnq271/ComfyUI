export const defaultGraph = {
  last_node_id: 3,
  last_link_id: 2,
  nodes: [
    {
      id: 1,
      type: "Input",
      pos: [200, 200],
      size: {
        0: 422.84503173828125,
        1: 164.31304931640625
      },
      flags: {},
      order: 2,
      mode: 0,
      outputs: [{
        name: "query",
        type: "TEXT",
        links: [1],
        slot_index: 0
      }],
      properties: {},
      widgets_values: [
	"Who is Elon Musk?"
      ],
    },
    {
      id: 2,
      type: "LLM",
      pos: [1235, 186],
      size: {
        0: 422.84503173828125,
        1: 164.31304931640625
      },
      flags: {},
      order: 2,
      mode: 0,
      inputs: [
	{
          name: "prompt",
          type: "TEXT",
          link: 2
	}	
      ],
      outputs: [{
        name: "text",
        type: "TEXT",
        links: [3],
        slot_index: 0
      }],
      properties: {},
      widgets_values: [
	"gpt-3.5-turbo",
	"You are an agent designed to summarize a paragraph."
      ],
    },
    {
      id: 3,
      type: "WikipediaSearch",
      pos: [815, 189],
      size: {
        0: 210,
        1: 26
      },
      flags: {},
      order: 6,
      mode: 0,
      inputs: [{
        name: "query",
        type: "TEXT",
        link: 1
      }],
      outputs: [{
        name: "prompt",
        type: "TEXT",
        links: [2],
        slot_index: 0
      }],      
      properties: {},
      widgets_values: [
	"en",
	3
      ],      
    },    
    {
      id: 4,
      type: "End",
      pos: [1754, 189],
      size: {
        0: 210,
        1: 26
      },
      flags: {},
      order: 6,
      mode: 0,
      inputs: [{
        name: "text",
        type: "TEXT",
        link: 3
      }],
      properties: {},
    },    
  ],
  links: [
    [1, 1, 0, 3, 0, "SEARCH"],
    [2, 3, 0, 2, 0, "LLM"],
    [3, 2, 0, 4, 0, "TEXT"],    
  ],
  groups: [],
  config: {},
  extra: {},
  version: 0.4,
};
