# Engineering Specification 208: Extended Drive/User Syntax

This consolidates the DU design in **BetterCPM Design Questions 3** and the subsequent accepted engineering decisions of 2026-10-09. It specifies target behavior; extended-set support is not claimed for current binaries.

Source: [BetterCPM Design Questions 3](https://chatgpt.com/c/6aae43de-1e54-83ee-b3dc-4bce983ef904).

The specification separates accepted syntax and implementation requirements from questions still requiring resolution. Earlier proposals superseded by later discussion are not retained as current requirements.

## 1. Purpose and domain

A DU identifies a drive and a user area on that drive. Extended DU syntax lets an aware utility select several such locations in one filespec, using individual DUs, comma-separated lists, and inclusive user ranges.

The selected design domain is **16 drives × 32 user areas**, or 512 possible DUs. Drives are A through P; user numbers are 0 through 31. The canonical selection representation is a **512-bit, 64-byte bitmap**. This is neither a 64-bit map nor a 65-byte map. Any additional parser flags or state are outside the bitmap.

The existing BetterCP/M implementation supports drive designators A–P and users 0–31. This logical domain does not imply that every drive is configured or available on a particular platform. Parsing accepts the logical domain; availability is handled by the adopting utility.

The DU selection and the filename or filename pattern are separate parts of a filespec. For example:

```text
[A0,B[3-7],D[-]]:*.COM
```

selects locations A0, B3 through B7, and D0 through D31, with `*.COM` as the filename pattern. The parser interprets the scope; the utility decides what to do with matching files.

## 2. Conventional DU inheritance

Conventional single-location interpretation is preserved. An omitted drive inherits the current drive, and an omitted user inherits the current user. An ordinary unqualified filename therefore uses the current DU. This inheritance describes the shared DU/filespec interpretation; a search utility's broader default policy is a separate question.

Most importantly, **a drive without an explicit user selection means the current user on that drive, not every user on that drive**.

Assuming the current user is 5:

| Form | Selection |
| --- | --- |
| `D:` | D5 |
| `D5:` | D5 |
| `D[-]:` | D0 through D31 |
| `[A0,B[3-7],D]:` | A0, B3 through B7, and D5 |

The bare `D` inside a compound list has the same inheritance as `D:` outside it. It does not inherit the user number from the preceding term. Likewise, closing a per-drive user list ends that list's drive context; the drive is not carried into subsequent compound-list terms.

An early assistant interpretation of `D` as all users was explicitly corrected. It must not be used in the final design.

Conventional user-only qualifiers such as `5:` are preserved. A bare user number is also valid as a compound-list term and inherits the caller's original drive, independently of preceding terms. The caller's drive and user are captured once before parsing.

For example, with caller DU B2:

```text
DIR [A0,C[3,5,7-11],5]:
```

selects A0, B5, C3, C5 and C7–C11. The final `5` inherits B, not C. Canonical enumeration is A0, B5, C3, C5, C7, C8, C9, C10, C11.

## 3. Single DU selections and user lists

An explicit drive/user pair selects one location:

```text
B4:FOO.COM
```

A drive may instead be followed by a bracketed, comma-separated list of user selections:

```text
B[4]:FOO.COM
B[4,7,11]:FOO.COM
B[2,5-8,11]:FOO.COM
```

Each list item is either one user number or a user range. A singleton list is valid. Lists can mix singleton users, closed ranges, and open-ended ranges:

```text
B[2,5-,11]:
B[-4,8-]:
B[9,4,11,2]:
```

The last expression is valid despite the arbitrary order of its entries. Its selection is B2, B4, B9, and B11. Its enumeration order is canonical, not the order typed.

## 4. Inclusive ranges

Ranges use `-` and include both endpoints.

```text
B[3-9]:
```

selects B3, B4, B5, B6, B7, B8, and B9.

Equal endpoints are valid:

```text
A[5-5]:
```

selects only A5.

### 4.1 Open endpoints

An omitted lower endpoint means 0. An omitted upper endpoint means the maximum supported user number, 31 in the selected model.

| Form | Users selected on B |
| --- | --- |
| `B[4-8]:` | 4 through 8 |
| `B[4-]:` | 4 through 31 |
| `B[-14]:` | 0 through 14 |
| `B[-]:` | 0 through 31 |

`-14` in a user list is an open lower endpoint, not a negative user number. A lone `-` is a valid range with both endpoints omitted; it is not an empty list item.

These forms all have identical meaning:

```text
D[0-31]:
D[0-]:
D[-31]:
D[-]:
```

Open ranges may appear anywhere a user-list item is permitted. They are not special cases restricted to an entire list.

### 4.2 Descending endpoints

Closed ranges with descending endpoints are accepted and normalized:

```text
B[3-9]:
B[9-3]:
```

Both select B3 through B9. For two explicit endpoints, the selected interval is from their minimum to their maximum, inclusive.

Descending spelling does not request descending processing. Input order has no operational meaning in the bitmap model.

Open endpoint semantics remain directional: `B[9-]:` means 9 through 31, and `B[-9]:` means 0 through 9. These are not reinterpreted as requests for reverse enumeration.

Earlier discussion rejected descending ranges. The later discussion replaced that restriction once the selection became an unordered bitmap. The earlier rejection is superseded.

## 5. Compound DU lists

Outer brackets enclose a comma-separated list of DU terms:

```text
[A0,B3,C7]:FOO.COM
[A,B,C]:*.COM
[A0,B[2,4],C[3-8],D5]:
[A0,B[2,4,7-11],C[-],D[5-],E[-8]]:*.COM
```

Each term is either a drive with an optional single user or bracketed user selection, or a bare user number inheriting the caller's original drive. A drive with no user inherits the current user. Every term contributes to the same set of selected DUs.

The outer list may contain one term. For example, `[A0]:` selects precisely A0.

The colon follows the complete DU scope. Examples with no filename, such as `DIR [A0]:`, demonstrate DU selection; the command's interpretation of a missing filename is outside the DU grammar.

### 5.1 No recursive compound lists

The grammar allows an outer compound DU list to contain per-drive user lists. It does **not** allow a compound DU list to contain another compound DU list.

Valid:

```text
[A0,B[3-7],D[-]]:
[B[4]]:
```

Invalid:

```text
[[A0,B0],C0]:
[[A0,B[3-7]],C0]:
[[A0,B4],C]:
[A,[B,C],D]:
```

The invalid expressions are not automatically flattened or repaired. The user must supply a valid equivalent, such as `[A0,B4,C]:`.

Conceptually, the outer `[` enters compound-DU mode. A `[` following a drive enters user-selection mode. The inner `]` closes that user selection; the outer `]` closes the compound scope. There is one internal user-list bracket level, or at most two simultaneously open bracket pairs when counting the outer delimiter.

A generic depth limit alone is insufficient: `[[A0,B0],C0]:` has only two bracket levels but is still invalid because the inner brackets introduce the wrong construct.

Earlier suggestions of three, four, or eight nesting levels, and accepting redundant nested compound grouping, were superseded by this reduced grammar.

## 6. Structural grammar

The following expresses the settled structure. Drive letters are case-insensitive. Spaces within selectors are rejected. User numbers have one or two decimal digits; leading zeros are permitted, but the numeric value must be 0–31.

```text
qualified-scope = scope ':'
scope           = du-term | compound-list
compound-list   = '[' du-term (',' du-term)* ']'
du-term         = drive [user-number | user-list] | user-number
user-list       = '[' user-item (',' user-item)* ']'
user-item       = user-number | user-range
user-range      = [user-number] '-' [user-number]
```

`drive` identifies one of the 16 drives, and `user-number` is within 0–31. Both range endpoints may be absent, but the hyphen must be present. A compound-list item cannot itself be a compound list. A user-list item cannot itself contain another list.

An absent qualifier selects the caller's current DU. A bare user-number qualifier or compound term inherits the original drive; a bare drive inherits the original user. User-only bracketed ranges are not introduced.

## 7. Equivalent forms

Composing the rules naturally gives different spellings of the same selection. Equivalent spellings must produce the same bitmap; they need not follow identical internal parsing paths.

All six forms below are valid and select only A5:

```text
A5:
A[5]:
[A5]:
A[5-5]:
[A[5]]:
[A[5-5]]:
```

Likewise:

```text
DIR A0:
DIR [A0]:
```

select the same DU, as do:

```text
DIR B4:
DIR B[4]:
DIR [B4]:
DIR [B[4]]:
```

Equivalent results also arise through duplicate entries, overlapping ranges, descending ranges, and explicit versus omitted range endpoints. Redundancy within valid grammar is accepted. Redundant recursive compound grouping remains invalid.

## 8. Bitmap semantics and canonical enumeration

Each possible DU corresponds to one membership bit. A set bit means selected; a clear bit means not selected. Parsing accumulates the union of all selected DUs.

Setting an already-set bit is harmless:

```text
bitmap[byte] := bitmap[byte] OR mask
```

Consequently:

```text
B[4,7,4]:
```

selects B4 and B7 once each, and:

```text
B[5-12,11,4-8]:
```

selects B4 through B12. No special duplicate detection, overlap analysis, sorting, or pre-merging of ranges is required. Each validated term can simply set the relevant bits.

Utilities enumerate selected locations in **drive-major, user-minor order**: A0 through A31, then B0 through B31, continuing through P31, skipping clear bits. Each selected DU is enumerated once. Input order, list order, and range direction do not alter that order.

The syntax can describe any nonempty subset of the 512 DUs, at least by explicitly listing every selected pair. The conversation described this as expressing any 64-byte map. Empty lists are rejected; the all-zero map is internal state only and has no textual selection form. The ordinary command-tail length also limits how large a literal selection can be written in one invocation.

The bitmap has four consecutive bytes per drive, in A–P order. For drive index d (A=0) and user u, byte index is `4*d + u//8`; bit index is `u%8`. User 0 is bit 0 of the first byte for its drive. The caller owns the 64-byte output buffer and iterator workspace; parser flags are separate.

`[*]` is retired and invalid as a user selector. `[-]` selects all users. This retirement does not change `*` in filename patterns.

## 9. Malformed syntax and validation

Every comma must separate two valid, nonempty elements. Leading commas, trailing commas, and consecutive commas are syntax errors in both user lists and compound DU lists.

Examples:

| Input | Result |
| --- | --- |
| `B[3,5]:` | Valid |
| `B[,3,5]:` | Syntax error |
| `B[5,9,]:` | Syntax error |
| `B[3,,5]:` | Syntax error |
| `B[,]:` | Syntax error |
| `B[,,,]:` | Syntax error |
| `B[]:` | Syntax error |
| `[,A0,B3]:` | Syntax error |
| `[A0,B3,]:` | Syntax error |
| `[A0,,B3]:` | Syntax error |
| `B[32]:` | User outside the selected domain |
| `[[A0,B4],C]:` | Unsupported recursive compound list |

Unbalanced brackets, invalid user-list nesting, malformed range items, invalid drive designators, and out-of-domain explicit user numbers must be rejected. Descending ranges, identical range endpoints, duplicate selections, and overlapping ranges are not errors.

The parser must validate the entire expression successfully before the utility acts on any selected DU. A malformed expression must not trigger partially completed file operations. Intermediate bits may be set while parsing, but they must not be consumed as a successful result after an error. On failure, the parser clears the complete selection bitmap and returns failure with an error code and input position. The caller must validate the entire invocation, including options and the filename pattern, before any operation.

## 10. Shared linkable parser library

Extended-filespec parsing shall be implemented as a reusable source-code/library module linked into utilities that require it. The common implementation is maintained once; each adopting utility incorporates it at build time.

It is not a required resident service, new BDOS facility, RSX dependency, or CCP expansion facility. The utility owns its operation and uses the parsed result internally. The bitmap belongs in transient utility workspace, not in a newly imposed global or resident interface.

The parser's responsibilities are to interpret and validate the scope, resolve inherited components, normalize the selected DUs into the canonical bitmap representation, and keep the filename pattern separate. Directory searching, opening files, displaying matches, and other disk operations belong to the caller.

For example, WHEREIS could enumerate selected DUs and search directory entries. FIND could use the same selection to search the contents of matching files. Sharing a parser does not require either utility to share operation semantics.

The conversation used conceptual operations such as `PARSE_FILESPEC` and `NEXT_DU`. These illustrate possible interfaces; they are not frozen entry-point names or calling conventions. The bitmap model and a common iterator are required; their exact calling conventions remain to be specified.

The initial implementation always constructs the bitmap, even for a single DU. A common iterator enumerates selected DUs in canonical order. The parser returns the bitmap and the remaining filename-pattern pointer and length, or failure with an error code and position. Exact register conventions remain to be specified.

The library begins as an internal shared assembly include, incorporated at build time. Each utility emits its parser routines once and supplies workspace. Macros may wrap inclusion or calls; the complete parser is not expanded at every call site. No resident service, RSX dependency or BDOS growth is required. A supported public programmer API may follow qualification.

Utilities that support only conventional filenames need not link the extended parser.

## 11. Legacy command-tail and FCB compatibility

The bitmap must not replace the CP/M command-tail or default-FCB interfaces. Conventional command-tail handling at `0080h` and compatible default FCB handling at `005Ch` and `006Ch`, as applicable, remain the execution contract for historical programs.

The CCP does not centrally expand an extended expression into repeated utility invocations or replace its command tail with hundreds of textual DU specifications. An aware utility parses the received arguments itself using the linked library.

Thus a conventional invocation such as:

```text
OLDUTIL C:FOO.COM
```

continues through the conventional interface. An invocation such as:

```text
OLDUTIL C[3-7]:FOO.COM
```

does not automatically acquire extended-syntax support. A historical utility may reject or misinterpret it. Extended interpretation is opt-in for programs written or adapted to use it.

An enhanced DIR may adopt the shared interpretation internally, but that does not change what unrelated transient programs receive. Nothing here establishes that the current DIR implementation already accepts all specified forms.

## 12. Adoption and remaining decisions

### 12.1 Accepted implementation and release boundaries

- Start adoption with transient DIR and STAT file inspection. Attribute changes and destructive utilities require their own operation contracts; set support does not automatically authorize them.
- Drive-wide STAT operations such as free-space status, DPB reporting and drive read-only assignment do not acquire per-user semantics. Their admitted selector forms must be documented separately.
- Keep the existing command-tail limit. Do not introduce an extended-input mechanism or CCP expansion into repeated invocations.
- Empty lists remain invalid. The all-zero bitmap is internal state, not a new textual empty-selection form.
- Preserve current CCP command-tail and default-FCB handling. Aware utilities parse their tails; this library does not change the legacy launch contract.
- Retain COPY's bounded 8.3 filename grammar: `?` consumes one position; terminal star runs fill the rest of a field; adjacent terminal stars collapse; characters after a star run within the same field are invalid. Name and extension are independent.
- A missing filename is interpreted by the utility, not the DU parser.

### 12.2 Remaining reconciliation and utility decisions

1. Reconcile older project descriptions with this controlling extended-selection grammar and explicitly mark superseded restrictions.
2. Specify parser entry-point names, registers, preserved registers, error-code values, input-position convention and iterator calling convention before implementation.
3. Specify exact selector/filename token boundaries and command option integration. Accepted lexical rules above must remain consistent across callers.
4. Define unavailable-location handling per operation. For DIR and STAT inspection, the recommended policy is a location-specific diagnostic followed by continuation to other selected locations.
5. WHEREIS default scope and `/ALL` policy remain separate decisions. Neither may change bare-drive inheritance. WHEREIS was selected for the System Disk; FIND remains a candidate for the Extra Utility Disk.
6. Determine which existing assembler include and relocatable-module conventions the implementation should reuse.
7. Decide later whether to expose the qualified library as a supported public programmer interface.

Open endpoints, normalized descending ranges, canonical order, duplicate collapse, user-only compound terms and retirement of `[*]` are accepted requirements, not unresolved options. This document does not declare all adopting utilities implemented or make every future adoption a new 1.0 prerequisite.
