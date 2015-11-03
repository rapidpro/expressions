var parser = new excellent.Parser('@', ['channel', 'contact', 'date', 'extra', 'flow', 'step']);

describe("finding expressions", function() {
    it("find expressions with and without parentheses", function() {
        expect(parser.expressions('Hi @contact.name from @(flow.sender)')).toEqual([
            {start: 3, end: 16, text: '@contact.name', closed: false}, 
            {start: 22, end: 36, text: '@(flow.sender)', closed: true}
        ]);
    });

    it("ignores invalid top levels", function() {
        expect(parser.expressions('Hi @contact.name from @nyaruka')).toEqual([
            {start: 3, end: 16, text: '@contact.name', closed: false}
        ]);
    });

    it("ignore parentheses inside string literals", function() {
        expect(parser.expressions('Hi @(LEN("))"))')).toEqual([
            {start: 3, end: 15, text: '@(LEN("))"))', closed: true}
        ]);
    });
});

describe("get expression context", function() {
    it("finds context for expression without parentheses", function() {
        expect(parser.expressionContext('Hi @contact.na')).toBe('contact.na');
    });

    it("finds context for expression with parentheses", function() {
        expect(parser.expressionContext('Hi @contact.name from @(flow.sen')).toBe('(flow.sen');
    });

    it("don't include a closed expression", function() {
        expect(parser.expressionContext('Hi @contact.name from @(flow.sender)')).toBeNull();
    });
});

describe("get auto-complete context", function() {
    it("finds context for expression without parentheses", function() {
        expect(parser.autoCompleteContext('Hi @contact.na')).toBe('contact.na');
    });

    it("finds context for expression with parentheses", function() {
        expect(parser.autoCompleteContext('Hi @contact.name from @(flow.sen')).toBe('flow.sen');
    });

    it("no context if last typed thing can't be an identifier", function() {
        expect(parser.autoCompleteContext('Hi @contact.name from @(flow.sender + ')).toBeNull();
    });

    it("no context if in a string literal", function() {
        expect(parser.autoCompleteContext('Hi @(CONCAT("@con')).toBeNull();
        expect(parser.autoCompleteContext('Hi @("!" & "@con')).toBeNull();
    });

    it("ignore parenthesis triggering functions completions for variables", function() {
        expect(parser.autoCompleteContext("Hi @(contact.age")).toBe('contact.age');
    });

    it('ignore the parenthesis triggering functions completions for functions', function() {
        expect(parser.autoCompleteContext("Hi @(SUM")).toBe('SUM');
    });

    it("matches the function without parameters", function() {
        expect(parser.autoCompleteContext("Hi @(SUM(")).toBe('SUM');
    });

    it("matches the function missing balanced parentheses", function() {
        expect(parser.autoCompleteContext("Hi @(SUM(dads, ABS(number))")).toBeNull();
        expect(parser.autoCompleteContext("Hi @(SUM(dads, ABS(number)")).toBe('SUM');
    });

    it("ignores trailing spaces in function parameters", function () {
        expect(parser.autoCompleteContext("Hi @(SUM( ")).toBe('SUM');
        expect(parser.autoCompleteContext("Hi @(SUM(   ")).toBe('SUM');
        expect(parser.autoCompleteContext("Hi @(SUM(dads, ABS(number))  ")).toBeNull();
        expect(parser.autoCompleteContext("Hi @(SUM(dads, ABS(number)  ")).toBe('SUM');
    });

    it("matches the variable in function parameters", function() {
        expect(parser.autoCompleteContext("Hi @(SUM(contact.date_added")).toBe('contact.date_added');
    });

    it('matches the function with incomplete parameters without trailing space', function () {
        expect(parser.autoCompleteContext("Hi @(SUM(contact.date_added,")).toBe('SUM');
    });

    it('matches the function with incomplete parameters with trailing space', function () {
        expect(parser.autoCompleteContext("Hi @(SUM(contact.date_added,  ")).toBe('SUM');
    });

    it('ignore the function with balanced parentheses', function(){
        expect(parser.autoCompleteContext("Hi @(SUM(contact.date_added, step)")).toBeNull();
        expect(parser.autoCompleteContext("Hi @(SUM(contact.date_added, ABS(step.value)")).toBe('SUM');
        expect(parser.autoCompleteContext("Hi @(SUM(contact.date_added, ABS(step.value))")).toBeNull();
    });

    it('ignore string literal in parameters', function () {
        expect(parser.autoCompleteContext('Hi @(SUM(contact.date_added, "foo ( bar",  step)')).toBeNull();
        expect(parser.autoCompleteContext('Hi @(SUM(contact.date_added, "foo ( bar", ABS(step.value)')).toBe('SUM');
    });

});
