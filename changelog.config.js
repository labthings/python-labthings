'use strict'

const mainTemplateStr = `{{> header}}

{{#each commitGroups}}

{{#if title}}
### {{title}}

{{/if}}
{{#each commits}}
{{> commit root=@root}}

{{/each}}
{{/each}}


`

const headerTemplateStr = `{{#if isPatch~}}
##
{{~else~}}
#
{{~/if}} {{#if @root.linkCompare~}}
[{{version}}](
{{~#if @root.repository~}}
  {{~#if @root.host}}
    {{~@root.host}}/
  {{~/if}}
  {{~#if @root.owner}}
    {{~@root.owner}}/
  {{~/if}}
  {{~@root.repository}}
{{~else}}
  {{~@root.repoUrl}}
{{~/if~}}
/compare/{{previousTag}}...{{currentTag}})
{{~else}}
{{~version}}
{{~/if}}
{{~#if title}} "{{title}}"
{{~/if}}
{{~#if date}} ({{date}})
{{/if}}`

const commitTemplateStr = `*{{#if scope}} **{{scope}}:**
{{~/if}} {{#if subject}}
  {{~subject}}
{{~else}}
  {{~header}}
{{~/if}}

{{~!-- commit link --}} {{#if @root.linkReferences~}}
  ([{{hash}}](
  {{~#if @root.repository}}
    {{~#if @root.host}}
      {{~@root.host}}/
    {{~/if}}
    {{~#if @root.owner}}
      {{~@root.owner}}/
    {{~/if}}
    {{~@root.repository}}
  {{~else}}
    {{~@root.repoUrl}}
  {{~/if}}/
  {{~@root.commit}}/{{hash}}))
{{~else}}
  {{~hash}}
{{~/if}}

{{~!-- commit references --}}
{{~#if references~}}
  , closes
  {{~#each references}} {{#if @root.linkReferences~}}
    [
    {{~#if this.owner}}
      {{~this.owner}}/
    {{~/if}}
    {{~this.repository}}#{{this.issue}}](
    {{~#if @root.repository}}
      {{~#if @root.host}}
        {{~@root.host}}/
      {{~/if}}
      {{~#if this.repository}}
        {{~#if this.owner}}
          {{~this.owner}}/
        {{~/if}}
        {{~this.repository}}
      {{~else}}
        {{~#if @root.owner}}
          {{~@root.owner}}/
        {{~/if}}
          {{~@root.repository}}
        {{~/if}}
    {{~else}}
      {{~@root.repoUrl}}
    {{~/if}}/
    {{~@root.issue}}/{{this.issue}})
  {{~else}}
    {{~#if this.owner}}
      {{~this.owner}}/
    {{~/if}}
    {{~this.repository}}#{{this.issue}}
  {{~/if}}{{/each}}
{{~/if}}`

module.exports = {
  writerOpts: {
    mainTemplate: mainTemplateStr,
    headerPartial: headerTemplateStr,
    commitPartial: commitTemplateStr
  }
}