# Sections: naming, slugs and where a component files

The component name and the section slug are derived from the title by two
different rules, and confusing them will make you mis-predict both:

- the **name** is the chosen segment with whitespace stripped;
- the **section** is the *raw* segment before it — `parts[idx - 1]`, not "the
  prefix" in general — lowercased with non-alphanumerics collapsed to `-`.

Whitespace survives into the slug, so `Media sync/` and `MediaSync/` produce
**two sections**, `media-sync` and `mediasync` — six components and two, and
nothing warned. (Strip whitespace first, as the name rule does, and both
collapse to `mediasync`; that is why getting this backwards hides the bug.)
For a three-segment title the name comes from the segment matching a real
export and the section from the one before it, so `Forms/Button/Sizes` is
`Button` in `forms`.

Grep every title prefix before an upload and read the list as a set.

When sections are wrong, file each component under **the section its actual
consumer names**, found by reading imports, not by where the file happens to
sit. A dialog opened from the library page belongs with the library even if it
lives in `components/editor/`. A section need not reproduce the filesystem.

**The consumer rule applies to feature components, not to primitives.** A
button, a card, a toast and a field are reached for by every section, so
"their consumer" names nothing. Those take a categorical taxonomy — Actions,
Forms, Surfaces, Feedback — and a single-member category there is fine;
`Actions/Button` reads better than burying the primitive every other section
uses inside `Forms/`. Expect a healthy system to be a hybrid: categorical for
the primitive layer, consumer-named for the feature layer. Judge a one-member
*feature* section harder than a one-member primitive one.

Two further judgments worth making deliberately:

- **A duplicate can dissolve rather than merge.** When two components carry the
  wrong spelling, one may belong to a different section entirely; moving it
  there removes the duplicate and fixes a misfiling at once.
- **Name maturity honestly.** A prototype published from a `prototypes/`
  directory should say so in its section. Rendering correctly is not promotion.
