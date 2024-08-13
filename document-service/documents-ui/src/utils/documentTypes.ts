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
      { type: 'COOP_MISC', description: 'Correction Filing', productCode: 'business' },
      { type: 'COFI', description: 'Cooperatives Miscellaneous Documents', productCode: 'business' }
    ]
  },
  {
    class: 'CORP',
    description: 'Corporations',
    prefixes: ['BC', 'C', 'QA', 'QB', 'QC', 'QD', 'QE'],
    documents: [
      { type: 'CORP_MISC', description: 'Corporations Miscellaneous Documents', productCode: 'business' },
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
      { type: 'LPRG', description: 'LP and LLP Registration', productCode: 'business' },
      { type: 'AMLO', description: 'Amalgamation Out', productCode: 'business' },
      { type: 'ASNU', description: 'Assumed Name Undertaking', productCode: 'business' },
      { type: 'AMAL', description: 'Update Due to Amalgamation', productCode: 'business' },
      { type: 'ATTN', description: 'Attorney', productCode: 'business' },
      { type: 'DISS', description: 'Dissolution Due to Death', productCode: 'business' }
    ]
  },
  {
    class: 'FIRM',
    description: 'Firms',
    prefixes: ['FM', 'GP', 'SP', 'MF'],
    documents: [
      { type: 'FIRM_MISC', description: 'Firms miscellaneous documents', productCode: 'business' },
      { type: 'CNVF', description: 'Conversion of Firm', productCode: 'business' },
      { type: 'COPN', description: 'Change of Proprietor\'s Name', productCode: 'business' }
    ]
  },
  {
    class: 'MHR',
    description: 'Manufactured Home Registry',
    prefixes: ['MH'],
    documents: [
      { type: 'MHR_MISC', description: 'MHR miscellaneous documents', productCode: 'mhr' },
      { type: 'FNCH', description: 'MH Supporting Documentation', productCode: 'mhr' },
      { type: 'MHSP', description: 'Finance Change Statements/Partial Discharges', productCode: 'mhr' },
      { type: 'REG_101', description: 'MANUFACTURED HOME REGISTRATION', productCode: 'mhr' },
      { type: 'REG_102', description: 'DECAL REPLACEMENT', productCode: 'mhr' },
      { type: 'REG_103', description: 'TRANSPORT PERMIT', productCode: 'mhr' },
      { type: 'ABAN', description: 'TRANSFER DUE TO ABANDONMENT AND SALE', productCode: 'mhr' },
      { type: 'ADDI', description: 'ADDITION', productCode: 'mhr' },
      { type: 'AFFE', description: 'TRANSFER TO EXECUTOR – ESTATE UNDER $25,000 WITH WILL', productCode: 'mhr' },
      { type: 'ATTA', description: 'ATTACHMENT', productCode: 'mhr' },
      { type: 'BANK', description: 'TRANSFER DUE TO BANKRUPTCY', productCode: 'mhr' },
      { type: 'CAU', description: 'NOTICE OF CAUTION', productCode: 'mhr' },
      { type: 'CAUC', description: 'CONTINUED NOTICE OF CAUTION', productCode: 'mhr' },
      { type: 'CAUE', description: 'EXTENSION TO NOTICE OF CAUTION', productCode: 'mhr' },
      { type: 'COMP', description: 'CERTIFICATE OF COMPANIES', productCode: 'mhr' },
      { type: 'COUR', description: 'COURT RESCIND ORDER', productCode: 'mhr' },
      { type: 'DEAT', description: 'TRANSFER TO SURVIVING JOINT TENANT(S)', productCode: 'mhr' },
      { type: 'DNCH', description: 'DECLARATION OF NAME CHANGE', productCode: 'mhr' },
      { type: 'EXMN', description: 'MANUFACTURED EXEMPTION', productCode: 'mhr' },
      { type: 'EXNR', description: 'NON-RESIDENTIAL EXEMPTION', productCode: 'mhr' },
      { type: 'EXRE', description: 'MANUFACTURED HOME RE-REGISTRATION', productCode: 'mhr' },
      { type: 'EXRS', description: 'RESIDENTIAL EXEMPTION', productCode: 'mhr' },
      { type: 'FORE', description: 'TRANSFER DUE TO FORECLOSURE ORDER', productCode: 'mhr' },
      { type: 'FZE', description: 'REGISTRARS FREEZE', productCode: 'mhr' },
      { type: 'GENT', description: 'TRANSFER DUE TO GENERAL TRANSMISSION', productCode: 'mhr' },
      { type: 'LETA', description: 'TRANSFER TO ADMINISTRATOR – GRANT OF PROBATE WITH NO WILL', productCode: 'mhr' },
      { type: 'MAID', description: 'MAIDEN NAME', productCode: 'mhr' },
      { type: 'MAIL', description: 'MAILING ADDRESS', productCode: 'mhr' },
      { type: 'MARR', description: 'MARRIAGE CERTIFICATE', productCode: 'mhr' },
      { type: 'NAMV', description: 'CERTIFICATE OF VITAL STATS', productCode: 'mhr' },
      { type: 'NCAN', description: 'CANCEL NOTE', productCode: 'mhr' },
      { type: 'NCON', description: 'CONFIDENTIAL NOTE', productCode: 'mhr' },
      { type: 'NPUB', description: 'PUBLIC NOTE', productCode: 'mhr' },
      { type: 'NRED', description: 'NOTICE OF REDEMPTION', productCode: 'mhr' },
      { type: 'PUBA', description: 'PUBLIC AMENDMENT', productCode: 'mhr' },
      { type: 'REBU', description: 'REBUILT', productCode: 'mhr' },
      { type: 'REGC', description: 'REGISTRAR\'S CORRECTION', productCode: 'mhr' },
      { type: 'REIV', description: 'TRANSFER DUE TO REPOSSESSION - INVOLUNTARY', productCode: 'mhr' },
      { type: 'REPV', description: 'TRANSFER DUE TO REPOSSESSION - VOLUNTARY', productCode: 'mhr' },
      { type: 'REST', description: 'RESTRAINING ORDER', productCode: 'mhr' },
      { type: 'STAT', description: 'REGISTERED LOCATION CHANGE', productCode: 'mhr' },
      { type: 'SZL', description: 'TRANSFER DUE TO SEIZURE UNDER LAND ACT', productCode: 'mhr' },
      { type: 'TAXN', description: 'NOTICE OF TAX SALE', productCode: 'mhr' },
      { type: 'TAXS', description: 'TRANSFER DUE TO TAX SALE', productCode: 'mhr' },
      { type: 'THAW', description: 'REMOVE FREEZE', productCode: 'mhr' },
      { type: 'TRAN', description: 'TRANSFER DUE TO SALE OR GIFT', productCode: 'mhr' },
      { type: 'VEST', description: 'TRANSFER DUE TO VESTING ORDER', productCode: 'mhr' },
      { type: 'WHAL', description: 'WAREHOUSEMAN LIEN', productCode: 'mhr' },
      { type: 'WILL', description: 'TRANSFER TO EXECUTOR - GRANT OF PROBATE WITH WILL', productCode: 'mhr' }
    ]
  },
  {
    class: 'NR',
    description: 'Name Requests',
    prefixes: ['NR'],
    documents: [
      { type: 'NR_MISC', description: 'Name requests miscellaneous documents', productCode: 'nro' },
      { type: 'CONS', description: 'NR Consent Letter', productCode: 'nro' }
    ]
  },
  {
    class: 'PPR',
    description: 'Personal Property Registry',
    prefixes: ['PPR'],
    documents: [
      { type: 'PPR_MISC', description: 'PPR miscellaneous documents', productCode: 'ppr' },
      { type: 'PPRS', description: 'PPR Search', productCode: 'ppr' },
      { type: 'PPRC', description: 'PPR Secure Party Codes', productCode: 'ppr' }
    ]
  },
  {
    class: 'SOCIETY',
    description: 'Societies',
    prefixes: ['S', 'XS', 'S-', 'XS-', 'S/', 'XS/'],
    documents: [
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
      { type: 'CERT', description: 'Certificates', productCode: 'business' },
      { type: 'LTR', description: 'Letter Templates', productCode: 'business' },
      { type: 'CLW', description: 'Client Letters', productCode: 'business' },
      { type: 'BYLW', description: 'Bylaw', productCode: 'business' },
      { type: 'CNST', description: 'Constitution', productCode: 'business' },
      { type: 'CONT', description: 'Consent', productCode: 'business' },
      { type: 'SYSR', description: 'System is the record', productCode: 'business' },
      { type: 'ADMN', description: 'Administration', productCode: 'business' },
      { type: 'RSLN', description: 'Resolution Document', productCode: 'business' },
      { type: 'AFDV', description: 'Affidavit Document', productCode: 'business' },
      { type: 'SUPP', description: 'Supporting Documents', productCode: 'business' },
      { type: 'MNOR', description: 'Minister\'s Order', productCode: 'business' },
      { type: 'FINM', description: 'Financial Management', productCode: 'business' },
      { type: 'APCO', description: 'Application to Correct the Registry', productCode: 'business' },
      { type: 'RPTP', description: 'Report of Payments', productCode: 'business' },
      { type: 'DAT', description: 'DAT or CAT', productCode: 'business' },
      { type: 'BYLT', description: 'Bylaw Alterations', productCode: 'business' },
      { type: 'CNVS', description: 'Conversions', productCode: 'business' },
      { type: 'CRTO', description: 'Court Orders', productCode: 'business' },
      { type: 'MEM', description: 'Membership', productCode: 'business' },
      { type: 'PRE', description: 'Pre Image Documents', productCode: 'business' },
      { type: 'REGO', description: 'Registrar\'s Order', productCode: 'business' },
      { type: 'PLNA', description: 'Plan of Arrangements', productCode: 'business' },
      { type: 'REGN', description: 'Registrar\'s Notation', productCode: 'business' },
      { type: 'FINC', description: 'Financial', productCode: 'business' },
      { type: 'BCGT', description: 'BC Gazette', productCode: 'business' },
      { type: 'CHNM', description: 'Change Of Name', productCode: 'business' },
      { type: 'OTP', description: 'OTP', productCode: 'business' }
    ]
  }
]
