const dragging_token_wrapper = $("#dragging_token_wrapper");

let drag_active = false;


class CursorTracker {
    static shared = new CursorTracker();
    #posx; #posy;

    constructor() {
        $(document).on("mousemove.cursor_tracker", function(event){this.#posx = event.clientX; this.#posy = event.clientY}.bind(this))
    }

    position() {return {"x": this.#posx, "y": this.#posy}}
}


class DrawBag {
    static shared = new DrawBag();
    #draw_bag;

    constructor() {
        this.#draw_bag = [];

        for (let type of [1,1, 2,2, 3,3, 4,4]) {
            for (let value of [1,2,3,4,5,6,7,8,9,10,11,12,13]) {
                this.#draw_bag.push([type, value]);
            }
        }

        this.#draw_bag.push([1, -1]);
        this.#draw_bag.push([4, -1]);

        this.#draw_bag.sort(() => Math.random() - 0.5);
    }

    get() {return this.#draw_bag.pop()} // TODO: draw bag empty case
}


class UniqueIDGenerator {
    static shared = new UniqueIDGenerator();
    #counter;

    constructor() {this.#counter = 0}

    generate() {
        const hash = this.#hash(this.#counter++); // Generate a hash based on the counter
        return this.#encodeToBase36(hash); // Convert the hash to an 8-character alphanumeric string
    }

    #hash(input) {
        // Simple deterministic hash function (e.g., DJB2)
        let hash = 5381;
        const str = input.toString();
        for (let i = 0; i < str.length; i++) hash = (hash * 33) ^ str.charCodeAt(i); // XOR and multiply
        return Math.abs(hash); // Ensure the hash is positive
    }

    #encodeToBase36(hash) {return hash.toString(36)} // Convert the hash to a base-36 alphanumeric string
}


class Token {
    #dom_element; #token_id; #token_color; #token_value; #parent;

    constructor() {
        this.#token_id = UniqueIDGenerator.shared.generate();
        [this.#token_color, this.#token_value] = DrawBag.shared.get();

        this.#dom_element = $(`<div class="game-token" id="${this.#token_id}" token-color="${this.#token_color}" token-value="${this.#token_value}"></div>`);
        this.#parent = null;

        this.initDrag()
    }

    getID() {return this.#token_id}
    getType() {return this.#token_color}
    getValue() {return this.#token_value}
    getDOM() {return this.#dom_element}

    getParent() {return this.#parent}
    setParent(parent) {return this.#parent = parent}

    initDrag() {this.#dom_element.on("mousedown.token_drag", this.drag.bind(this))}

    drag() {
        if (drag_active) return;
        drag_active = true;

        const token_width = this.#dom_element.width(),
              token_height = this.#dom_element.height(),
              original_parent = this.#dom_element.parent();

        this.#dom_element.appendTo(dragging_token_wrapper);

        this.#dom_element.css({
            left: CursorTracker.shared.position().x - token_width / 2,
            top: CursorTracker.shared.position().y - token_height / 2
        });

        let separators = $(".game-board-separator").toArray().map(e => [$(e), e.getBoundingClientRect()])

        console.log(separators)
        
        $(document).on("mousemove.token_drag", function(event) {
            this.#dom_element.css({
                left: event.clientX - token_width / 2,
                top: event.clientY - token_height / 2
            });

            let token_position = this.#dom_element.get(0).getBoundingClientRect();

            for (let separator of separators) {
                let overlap_x = token_position.left < separator[1].right && token_position.right > separator[1].left;
                let overlap_y = token_position.top < separator[1].bottom && token_position.bottom > separator[1].top;

                if (overlap_x && overlap_y) separator[0].addClass("visible").attr("title","Drop Token Here")
                else separator[0].removeClass("visible").attr("title","")
             }

        }.bind(this));

        $(document).on("mouseup.token_drag", this.drop.bind(this,original_parent));
    }

    drop(original_parent) {
        if (!drag_active) return;
        drag_active = false;

        $(document).off("mousemove.token_drag");
        $(document).off("mouseup.token_drag");

        // Check if the token is dropped on a valid cell
        const cell = $(".game-board-cell, .game-deck-cell").filter(function() {
            const cell_offset = $(this).offset(),
                  cell_width = $(this).width(),
                  cell_height = $(this).height();

            return event.clientX >= cell_offset.left && event.clientX <= cell_offset.left + cell_width &&
                   event.clientY >= cell_offset.top && event.clientY <= cell_offset.top + cell_height &&
                   !$(this).children().length;
        });

        // Check if the token is dropped on a separator that has cells next to it
        const separator = $(".game-board-separator").filter(function() {
            const separator_offset = $(this).offset(),
                  separator_width = $(this).width(),
                  separator_height = $(this).height();

            const position_valid = event.clientX >= separator_offset.left && event.clientX <= separator_offset.left + separator_width &&
                                   event.clientY >= separator_offset.top && event.clientY <= separator_offset.top + separator_height;

            if (!position_valid) return false;

            return ($(this).prev().hasClass("game-board-cell") && $(this).prev().children().length) ||
                   ($(this).next().hasClass("game-board-cell") && $(this).next().children().length);
        });

        console.log(separator)

        if (cell.length) cell.append(this.#dom_element);
        else if (separator.length) this.#dom_element.appendTo(original_parent) // TODO: Implement separator logic
        else this.#dom_element.appendTo(original_parent);
        
        this.#dom_element.css({left: "", top: ""});
    }

}


class GameDeck {
    static shared = new GameDeck();
    #dom_element; #cells; #tokens;

    constructor() {
        this.#dom_element = $(".game-deck-wrapper .game-deck");
        this.#cells = []; this.#tokens = [];

        this.createDOM();
        this.drawTokens();
    }

    createDOM() {
        let element;
        for (let i=0; i < 14; i++) {
            element = $(`<div class="game-deck-cell"></div>`);
            this.#dom_element.append(element);
            this.#cells.push(element);
        }
    }

    drawTokens() {
        let token;
        for (let cell of this.#cells) {
            token = new Token();
            token.getDOM().appendTo(cell);
            token.setParent(this);

            this.#tokens.push(token);
        }
    }

    getCells() {return this.#cells}
    getTokens() {return this.#tokens}
}

function separate_tiles() {
    const e = $(this);

    console.log(e)
}



$(window).on("load", function() {

    // Handler for showing and hiding separators that split groups
    $(document).on("mousemove.separator_handler", function(event) {

        $(".game-board-separator").each(function() {
            const e = $(this),
                  separator_offset = e.offset(),
                  separator_width = e.width(),
                  separator_height = e.height();
    
            const position_valid = event.clientX >= separator_offset.left && event.clientX <= separator_offset.left + separator_width &&
                                   event.clientY >= separator_offset.top && event.clientY <= separator_offset.top + separator_height;

            if (!position_valid) {
                e.removeClass("separate").attr("title","").off("mousedown.separate_tiles")
                return;
            }

            const tokens_valid = e.prev().children().length && e.next().children().length;
            
            if (tokens_valid && !e.hasClass("separate")) e.addClass("separate").attr("title","Separate Tiles").on("mousedown.separate_tiles", separate_tiles)
            
        })
    })

})