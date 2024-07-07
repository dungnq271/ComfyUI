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
        name: "user_message",
        type: "TEXT",
        links: [1],
        slot_index: 0
      }],
      properties: {},
      widgets_values: [
	"Who is Elon Musk?"
      ],
    },
    // {
    //   id: 2,
    //   type: "LLM",
    //   pos: [1235, 186],
    //   size: {
    //     0: 422.84503173828125,
    //     1: 164.31304931640625
    //   },
    //   flags: {},
    //   order: 2,
    //   mode: 0,
    //   inputs: [
    // 	{
    //       name: "prompt",
    //       type: "TEXT",
    //       link: 2
    // 	}	
    //   ],
    //   outputs: [{
    //     name: "text",
    //     type: "TEXT",
    //     links: [3],
    //     slot_index: 0
    //   }],
    //   properties: {},
    //   widgets_values: [
    // 	"claude-3-haiku-20240307",
    // 	"You are an agent designed to summarize a paragraph."
    //   ],
    // },
    {
      id: 2,
      type: "Search",
      pos: [815, 189],
      size: {
        0: 315,
        1: 50
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
        name: "nodes",
        type: "NODE",
        links: [2],
        slot_index: 0
      }],      
      properties: {},
      widgets_values: [
	"wikipedia",
      ],      
    },    
    {
      id: 3,
      type: "Response",
      // pos: [1754, 189],
      pos: [1435, 186],
      size: {
        0: 422,
        1: 164
      },
      flags: {},
      order: 6,
      mode: 0,
      inputs: [{
        name: "nodes",
        type: "NODE",
        link: 2
      }],
      properties: {},
      widgets_values: [
	"claude-3-haiku-20240307",
	// "You are an agent designed to summarize a paragraph."
      ],      
    },    
  ],
  links: [
    [1, 1, 0, 2, 0, "SEARCH"],
    [2, 2, 0, 3, 0, "RESPONSE"],
  ],
  groups: [],
  config: {},
  extra: {},
  version: 0.4,
};
