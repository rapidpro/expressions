# RapidPro Expressions

RapidPro messages and flows can contain expressions which are evaluated at runtime. These come in two flavours: simple and advanced.

## Simple Syntax

This is used to embed single values, e.g.

```
Hi @contact, you entered @flow.age for age. Is this correct?
```

## Advanced Syntax

This is used to build more complex expressions using similar syntax to Excel formulae, e.g.

```
Hi @(PROPER(contact)), you are @(YEAR(NOW()) - flow.year_born) years old. Is this correct?
```
