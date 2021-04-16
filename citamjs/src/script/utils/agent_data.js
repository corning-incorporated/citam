/**
 * A Frame corresponds to all positions at a given point in time.
 */

export class Frame {
    constructor(stepNumber, nAgents) {
        this.stepNumber = stepNumber;
        this.agentPositions = [];
        for (let i = 0; i < nAgents; i++) {
            this.agentPositions.push(new AgentPosition(i))
        }

    }
}

/**
 * Class to hold position of an agent. 
 */

export class AgentPosition {
    constructor(agentID) {
        this.id = agentID;
        this.x = null;
        this.y = null;
        this.floor = null;
        this.count = null;
        this.agentType = null;
    }

    setPosition(x, y, floor) {
        this.x = x;
        this.y = y;
        this.floor = floor;
    }

    setCount(count) {
        this.count = count;
    }

    setAgentType(agentType) {
        this.agentType = agentType;
    }
}
