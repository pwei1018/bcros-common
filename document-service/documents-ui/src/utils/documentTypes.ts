import type { DocumentClassIF } from '~/interfaces/document-types-interface'

/**
 * @file documentTypes.ts
 * @description Exports an object categorizing document types by entity type. Each category includes:
 * - `class`: Entity class.
 * - `prefixes`: Array of document prefixes.
 * - `documents`: Array of document details (type, description, product code).
 */
export const documentTypes: Array<DocumentClassIF> = [
  {
    class: 'COOP',
    description: 'Cooperatives',
    prefixes: ['CP', 'XCP'],
    documents: [
      { type: 'CONT', description: 'Consent', productCode: 'business' },
      { type: 'CORR', description: 'Correspondence', productCode: 'business' },
      { type: 'COOP_MISC', description: 'Correction Filing', productCode: 'business' },
      { type: 'COFI', description: 'Cooperatives Miscellaneous Documents', productCode: 'business' }
    ]
  },
  {
    class: 'CORP',
    description: 'Corporations',
    prefixes: ['BC', 'C', 'QA', 'QB', 'QC', 'QD', 'QE'],
    documents: [
      { type: 'APCO', description: 'Application to Correct the Registry', productCode: 'business' },
      { type: 'CERT', description: 'Certificates', productCode: 'business' },
      { type: 'CLW', description: 'Client Letters', productCode: 'business' },
      { type: 'CNVS', description: 'Conversions', productCode: 'business' },
      { type: 'CONT', description: 'Consent', productCode: 'business' },
      { type: 'CORR', description: 'Correspondence', productCode: 'business' },
      { type: 'COU', description: 'Court Order', productCode: 'business' },
      { type: 'CRTO', description: 'Court Orders', productCode: 'business' },
      { type: 'CORP_MISC', description: 'Corporations Miscellaneous Documents', productCode: 'business' },
      { type: 'DIRS', description: 'Directors', productCode: 'business' },
      { type: 'LTR', description: 'Letter Templates', productCode: 'business' },
      { type: 'MNOR', description: 'Minister\'s Order', productCode: 'business' },
      { type: 'NATB', description: 'Nature of Business', productCode: 'business' },
      { type: 'PLNA', description: 'Plan of Arrangements', productCode: 'business' },
      { type: 'REGN', description: 'Registrar\'s Notation', productCode: 'business' },
      { type: 'REGO', description: 'Registrar\'s Order', productCode: 'business' },
      { type: 'SUPP', description: 'Supporting Documents', productCode: 'business' },
      { type: 'SYSR', description: 'System is the record', productCode: 'business' },
      { type: 'FILE', description: 'COLIN Filing', productCode: 'business' },
      { type: 'DISD', description: 'Dissolution Delays', productCode: 'business' },
      { type: 'FRMA', description: 'Form 2\'s Address Change for Corps', productCode: 'business' },
      { type: 'AMLG', description: 'Amalgamations', productCode: 'business' },
      { type: 'CNTI', description: 'Continuation In', productCode: 'business' },
      { type: 'CNTO', description: 'Continuation Out', productCode: 'business' },
      { type: 'RSRI', description: 'Restoration/Reinstatement', productCode: 'business' },
      { type: 'COFF', description: 'CORPS Filed Forms', productCode: 'business' },
      { type: 'COSD', description: 'CORPS Supporting Documentation', productCode: 'business' },
      { type: 'CNTA', description: 'Continuation in Authorization', productCode: 'business' },
      { type: 'AMLO', description: 'Amalgamation Out', productCode: 'business' },
      { type: 'ASNU', description: 'Assumed Name Undertaking', productCode: 'business' },
      { type: 'AMAL', description: 'Update Due to Amalgamation', productCode: 'business' },
      { type: 'ATTN', description: 'Attorney', productCode: 'business' },
      { type: 'INV', description: 'Investigation', productCode: 'business' }
    ]
  },
  {
    class: 'FIRM',
    description: 'Firms',
    prefixes: ['FM', 'GP', 'SP', 'MF'],
    documents: [
      { type: 'CONT', description: 'Consent', productCode: 'business' },
      { type: 'CORR', description: 'Correspondence', productCode: 'business' },
      { type: 'FIRM_MISC', description: 'Firms miscellaneous documents', productCode: 'business' },
      { type: 'CNVF', description: 'Conversion of Firm', productCode: 'business' },
      { type: 'COPN', description: 'Change of Proprietor\'s Name', productCode: 'business' },
      { type: 'DISS', description: 'Dissolution Due to Death', productCode: 'business' }
    ]
  },
  {
    class: 'LP_LLP',
    description: 'Limited Partnership/Limited Liability Partnership',
    prefixes: ['LL', 'LP', 'XL', 'XP'],
    documents: [
      { type: 'ADDR', description: 'Address', productCode: 'business' },
      { type: 'ANNR', description: 'Annual Report', productCode: 'business' },
      { type: 'ATTN', description: 'Attorney', productCode: 'business' },
      { type: 'CORR', description: 'Correspondence', productCode: 'business' },
      { type: 'FILE', description: 'COLIN Filing', productCode: 'business' },
      { type: 'CHNM', description: 'Change Of Name', productCode: 'business' },
      { type: 'CONT', description: 'Consent', productCode: 'business' },
      { type: 'CNVF', description: 'Conversion of Firm', productCode: 'business' },
      { type: 'LPRG', description: 'LP and LLP Registration', productCode: 'business' }
    ]
  },
  {
    class: 'NR',
    description: 'Name Requests',
    prefixes: ['NR'],
    documents: [
      { type: 'CONT', description: 'Consent', productCode: 'business' },
      { type: 'CORR', description: 'Correspondence', productCode: 'business' },
      { type: 'NR_MISC', description: 'Name requests miscellaneous documents', productCode: 'nro' },
      { type: 'CONS', description: 'NR Consent Letter', productCode: 'nro' }
    ]
  },
  {
    class: 'SOCIETY',
    description: 'Societies',
    prefixes: ['S', 'XS', 'S-', 'XS-', 'S/', 'XS/'],
    documents: [
      { type: 'AFDV', description: 'Affidavit Document', productCode: 'business' },
      { type: 'APCO', description: 'Application to Correct the Registry', productCode: 'business' },
      { type: 'BYLT', description: 'Bylaw Alterations', productCode: 'business' },
      { type: 'BYLW', description: 'Bylaw', productCode: 'business' },
      { type: 'CERT', description: 'Certificates', productCode: 'business' },
      { type: 'CLW', description: 'Client Letters', productCode: 'business' },
      { type: 'CNST', description: 'Constitution', productCode: 'business' },
      { type: 'CNVS', description: 'Conversions', productCode: 'business' },
      { type: 'CONT', description: 'Consent', productCode: 'business' },
      { type: 'CRTO', description: 'Court Orders', productCode: 'business' },
      { type: 'LTR', description: 'Letter Templates', productCode: 'business' },
      { type: 'MNOR', description: 'Minister\'s Order', productCode: 'business' },
      { type: 'OTP', description: 'OTP', productCode: 'business' },
      { type: 'PLNA', description: 'Plan of Arrangements', productCode: 'business' },
      { type: 'REGN', description: 'Registrar\'s Notation', productCode: 'business' },
      { type: 'REGO', description: 'Registrar\'s Order', productCode: 'business' },
      { type: 'RSLN', description: 'Resolution Document', productCode: 'business' },
      { type: 'SUPP', description: 'Supporting Documents', productCode: 'business' },
      { type: 'SYSR', description: 'System is the record', productCode: 'business' },
      { type: 'SOC_MISC', description: 'Societies miscellaneous documents', productCode: 'business' },
      { type: 'SOCF', description: 'Society Filing', productCode: 'business' },
      { type: 'CORC', description: 'Corrections', productCode: 'business' },
      { type: 'ADDR', description: 'Address', productCode: 'business' },
      { type: 'ANNR', description: 'Annual Report', productCode: 'business' },
      { type: 'CORR', description: 'Correspondence', productCode: 'business' },
      { type: 'DIRS', description: 'Directors', productCode: 'business' }
    ]
  },
  {
    class: 'OTHER',
    description: 'Other',
    prefixes: [],
    documents: [
      { type: 'ADMN', description: 'Administration', productCode: 'business' },
      { type: 'FINM', description: 'Financial Management', productCode: 'business' },
      { type: 'RPTP', description: 'Report of Payments', productCode: 'business' },
      { type: 'FINC', description: 'Financial', productCode: 'business' },
      { type: 'BCGT', description: 'BC Gazette', productCode: 'business' }
    ]
  },
  {
    class: 'MHR',
    description: 'Manufactured Home Registry',
    prefixes: ['MH'],
    documents: [
      { type: 'AFDV', description: 'Affidavit Document', productCode: 'business' },
      { type: 'CLW', description: 'Client Letters', productCode: 'business' },
      { type: 'CONT', description: 'Consent', productCode: 'business' },
      { type: 'CORR', description: 'Correspondence', productCode: 'business' },
      { type: 'CORSP', description: 'Correspondence - MHR', productCode: 'business' },
      { type: 'CRTO', description: 'Court Orders', productCode: 'business' },
      { type: 'DAT', description: 'DAT or CAT', productCode: 'business' },
      { type: 'MEAM', description: 'Certificate of Merger or Amalgamation', productCode: 'business' },
      { type: 'MEM', description: 'Membership', productCode: 'business' },
      { type: 'PRE', description: 'Pre Image Documents', productCode: 'business' },
      { type: 'MHR_MISC', description: 'MHR Miscellaneous Documents', productCode: 'mhr' },
      { type: 'FNCH', description: 'MH Supporting Documentation', productCode: 'mhr' },
      { type: 'MHSP', description: 'Finance Change Statements/Partial Discharges', productCode: 'mhr' },
      { type: 'REG_101', description: 'Manufactured Home Registration', productCode: 'mhr' },
      { type: 'REG_102', description: 'Decal Replacement', productCode: 'mhr' },
      { type: 'REG_103', description: 'Transport Permit', productCode: 'mhr' },
      { type: 'ABAN', description: 'Transfer Due To Abandonment And Sale', productCode: 'mhr' },
      { type: 'ADDI', description: 'Addition', productCode: 'mhr' },
      { type: 'AFFE', description: 'Transfer To Executor – Estate Under $25,000 With Will', productCode: 'mhr' },
      { type: 'ATTA', description: 'Attachment', productCode: 'mhr' },
      { type: 'BANK', description: 'Transfer Due To Bankruptcy', productCode: 'mhr' },
      { type: 'CAU', description: 'Notice Of Caution', productCode: 'mhr' },
      { type: 'CAUC', description: 'Continued Notice Of Caution', productCode: 'mhr' },
      { type: 'CAUE', description: 'Extension To Notice Of Caution', productCode: 'mhr' },
      { type: 'COMP', description: 'Certificate Of Companies', productCode: 'mhr' },
      { type: 'COUR', description: 'Court Rescind Order', productCode: 'mhr' },
      { type: 'DEAT', description: 'Transfer To Surviving Joint Tenant(s)', productCode: 'mhr' },
      { type: 'DNCH', description: 'Declaration Of Name Change', productCode: 'mhr' },
      { type: 'EXMN', description: 'Manufactured Exemption', productCode: 'mhr' },
      { type: 'EXNR', description: 'Non-Residential Exemption', productCode: 'mhr' },
      { type: 'EXRE', description: 'Manufactured Home Re-Registration', productCode: 'mhr' },
      { type: 'EXRS', description: 'Residential Exemption', productCode: 'mhr' },
      { type: 'FORE', description: 'Transfer Due To Foreclosure Order', productCode: 'mhr' },
      { type: 'FZE', description: 'Registrars Freeze', productCode: 'mhr' },
      { type: 'GENT', description: 'Transfer Due To General Transmission', productCode: 'mhr' },
      { type: 'LETA', description: 'Transfer To Administrator – Grant Of Probate With No Will', productCode: 'mhr' },
      { type: 'MAID', description: 'Maiden Name', productCode: 'mhr' },
      { type: 'MAIL', description: 'Mailing Address', productCode: 'mhr' },
      { type: 'MARR', description: 'Marriage Certificate', productCode: 'mhr' },
      { type: 'NAMV', description: 'Certificate Of Vital Stats', productCode: 'mhr' },
      { type: 'NCAN', description: 'Cancel Note', productCode: 'mhr' },
      { type: 'NCON', description: 'Confidential Note', productCode: 'mhr' },
      { type: 'NPUB', description: 'Public Note', productCode: 'mhr' },
      { type: 'NRED', description: 'Notice Of Redemption', productCode: 'mhr' },
      { type: 'PUBA', description: 'Public Amendment', productCode: 'mhr' },
      { type: 'REBU', description: 'Rebuilt', productCode: 'mhr' },
      { type: 'REGC', description: 'Registrar\'s Correction', productCode: 'mhr' },
      { type: 'REIV', description: 'Transfer Due To Repossession - Involuntary', productCode: 'mhr' },
      { type: 'REPV', description: 'Transfer Due To Repossession - Voluntary', productCode: 'mhr' },
      { type: 'REST', description: 'Restraining Order', productCode: 'mhr' },
      { type: 'STAT', description: 'Registered Location Change', productCode: 'mhr' },
      { type: 'SZL', description: 'Transfer Due To Seizure Under Land Act', productCode: 'mhr' },
      { type: 'TAXN', description: 'Notice Of Tax Sale', productCode: 'mhr' },
      { type: 'TAXS', description: 'Transfer Due To Tax Sale', productCode: 'mhr' },
      { type: 'THAW', description: 'Remove Freeze', productCode: 'mhr' },
      { type: 'TRAN', description: 'Transfer Due To Sale Or Gift', productCode: 'mhr' },
      { type: 'VEST', description: 'Transfer Due To Vesting Order', productCode: 'mhr' },
      { type: 'WHAL', description: 'Warehouseman Lien', productCode: 'mhr' },
      { type: 'WILL', description: 'Transfer To Executor - Grant Of Probate With Will', productCode: 'mhr' }
    ]
  },
  {
    class: 'PPR',
    description: 'Personal Property Registry',
    prefixes: ['PPR'],
    documents: [
      { type: 'CONT', description: 'Consent', productCode: 'business' },
      { type: 'CORR', description: 'Correspondence', productCode: 'business' },
      { type: 'DAT', description: 'DAT or CAT', productCode: 'business' },
      { type: 'MEM', description: 'Membership', productCode: 'business' },
      { type: 'PRE', description: 'Pre Image Documents', productCode: 'business' },
      { type: 'PPR_MISC', description: 'PPR miscellaneous documents', productCode: 'ppr' },
      { type: 'PPR', description: 'PPR (Register Discharges)', productCode: 'ppr' },
      { type: 'PPRS', description: 'PPR Search', productCode: 'ppr' },
      { type: 'PPRC', description: 'PPR Secure Party Codes', productCode: 'ppr' }
    ]
  },
]

export const documentResultColumns: Array<TableColumnIF> = [
    {
      key: 'emptyColumn',
      label: 'Sort By',
      isFixed: true
    },
    {
      key: 'consumerDocumentId',
      label: 'Document ID',
      tooltipText: `The Document ID, also known as the Barcode Number, is a unique identifier assigned to a document
       record.`,
      sortable: true
    },
    {
      key: 'consumerIdentifier',
      label: 'Entity ID',
      tooltipText: `The Entity ID is a unique identifier assigned to an entity, such as a business or society.`,
      sortable: true
    },
    {
      key: 'consumerFilenames',
      label: 'Documents'
    },
    {
      key: 'documentTypeDescription',
      label: 'Document Type'
    },
    {
      key: 'consumerFilingDateTime',
      label: 'Filing Date'
    },
    {
      key: 'description',
      label: 'Document Description'
    },
    {
      key: 'actions',
      label: 'Actions',
      isFixed: true
    }
  ]

export const documentRecordHelpContent = `
  Lorem ipsum dolor sit amet, consectetur adipiscing elit. 
  Quisque maximus turpis luctus, 
  finibus dolor non, cursus nulla. 
  Nulla laoreet neque vestibulum malesuada luctus. 
  Donec fringilla metus neque,
  et hendrerit mi lacinia sed. Mauris eu euismod purus. 
  In lacinia nunc vel est placerat sodales a porttitor sem. 
  Sed tincidunt ligula nec odio iaculis, 
  in imperdiet dolor facilisis. Nam in varius turpis. 
  Vestibulum dignissim ipsum vel dui feugiat rhoncus. 
  Cras hendrerit lacinia arcu vitae posuere. 
  Phasellus vitae erat vel diam congue semper. 
  Nam vel mollis ex. Pellentesque augue augue, 
  blandit vestibulum arcu sit amet, 
  interdum lacinia lectus. Suspendisse eleifend lectus lorem, 
  tristique tincidunt lorem egestas non. Sed et rutrum justo. Proin est nunc, 
  luctus at est eget, rhoncus auctor enim.
  Mauris eget nunc ut dolor rhoncus vehicula. 
  Curabitur molestie eu ante et egestas. Etiam vitae laoreet tellus, et interdum elit. 
  Fusce vitae rhoncus lorem, id mattis purus. 
  Sed porttitor magna nec urna bibendum, sit amet blandit justo tristique. 
  Suspendisse at turpis vel elit posuere elementum et quis libero. 
  Aliquam vehicula dignissim maximus. Quisque accumsan iaculis euismod. 
  Maecenas magna eros, auctor et consequat ac, pretium eget leo. 
  Pellentesque in mauris dictum, elementum purus sed, sollicitudin dui. 
  Donec purus odio, commodo sed commodo a, rhoncus eu turpis. 
  Nullam porta maximus orci non ullamcorper.
`
