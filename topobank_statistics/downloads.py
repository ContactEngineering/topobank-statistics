"""
Place here all download function and register with @register_download_function
"""
import io

import pandas as pd
import pint
from django.http import HttpResponse
from django.utils.text import slugify

from topobank.analysis.registry import register_download_function
from topobank.analysis.downloads import publications_urls, analyses_meta_data_dataframe, analysis_header_for_txt_file

from .functions import VIZ_ROUGHNESS_PARAMETERS


def roughness_parameters_data_frame(analyses):
    # Unit conversion
    ureg = pint.UnitRegistry()
    ureg.default_format = '~P'

    # Collect data
    data = []
    for analysis in analyses:
        result = analysis.result
        topography = analysis.subject

        row = {
            'Digital surface twin': topography.surface.name,
            'Measurement': topography.name,
            'Creator': topography.creator,
            'Instrument name': topography.instrument_name,
            'Instrument type': topography.instrument_type,
            'Instrument parameters': topography.instrument_parameters
        }
        for quantity in result:
            v = ureg.Quantity(quantity['value'], 'dimensionless' if quantity['unit'] == 1 else quantity['unit'])
            v_si = v.to_base_units()  # Convert to SI units

            quantity_header = quantity['quantity']
            if quantity['from']:
                quantity_header += ', ' + quantity['from']
            if quantity['direction']:
                quantity_header += ', ' + quantity['direction']
            if quantity['symbol']:
                quantity_header = quantity['symbol'].replace(r'&Delta;', 'Δ') + ' [' + quantity_header + ']'
            quantity_header += f' ({v_si.units})'

            row |= {quantity_header: v_si.magnitude}
        data += [row]

    # Return data frame
    df = pd.DataFrame(data)

    return df


@register_download_function(VIZ_ROUGHNESS_PARAMETERS, 'results', 'csv')
def download_roughness_parameters_to_txt(request, analyses):
    """Download roughness parameters from given analyses as CSV file.

       Tables with roughness parameters only make sense for analyses
       where subject is a topography (so far). All other analyses
       (e.g. for surfaces) will be ignored here.

        Parameters
        ----------
        request
            HTTPRequest
        analyses
            Sequence of Analysis instances

        Returns
        -------
        HTTPResponse
    """
    # TODO: It would probably be useful to use the (some?) template engine for this.
    # TODO: We need a mechanism for embedding references to papers into output.

    # Only use analyses which are related to a specific topography
    analyses = [a for a in analyses if a.is_topography_related]

    # Collect publication links, if any
    publication_urls = publications_urls(request, analyses)

    # Pack analysis results into a single text file.
    f = io.StringIO()
    for i, analysis in enumerate(analyses):
        if i == 0:
            f.write('# {}\n'.format(analysis.function) +
                    '# {}\n'.format('=' * len(str(analysis.function))))

            f.write('# IF YOU USE THIS DATA IN A PUBLICATION, PLEASE CITE XXX.\n' +
                    '#\n')
            if len(publication_urls) > 0:
                f.write('#\n')
                f.write('# For these analyses, published data was used. Please visit these URLs for details:\n')
                for pub_url in publication_urls:
                    f.write(f'# - {pub_url}\n')
                f.write('#\n')

        f.write(analysis_header_for_txt_file(analysis))

    f.write('# Table of roughness parameters\n')
    df = roughness_parameters_data_frame(analyses)
    df.to_csv(f, sep=';', index=False)
    f.write('\n')

    # Prepare response object.
    response = HttpResponse(f.getvalue(), content_type='application/text')
    filename = '{}.csv'.format(analysis.function.name.replace(' ', '_'))
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Close file and return response.
    f.close()
    return response


@register_download_function(VIZ_ROUGHNESS_PARAMETERS, 'results', 'xlsx')
def download_roughness_parameters_to_xlsx(request, analyses):
    """Download roughness parameters from given analyses as XLSX file.

       Tables with roughness parameters only make sense for analyses
       where subject is a topography (so far). All other analyses
       (e.g. for surfaces) will be ignored here.

        Parameters
        ----------
        request
            HTTPRequest
        analyses
            Sequence of Analysis instances

        Returns
        -------
        HTTPResponse
    """
    analyses = [a for a in analyses if a.is_topography_related]

    f = io.BytesIO()
    excel = pd.ExcelWriter(f)

    roughness_df = roughness_parameters_data_frame(analyses)
    roughness_df.to_excel(excel, sheet_name="Roughness parameters", index=False)
    info_df = analyses_meta_data_dataframe(analyses, request)
    info_df.to_excel(excel, sheet_name='INFORMATION', index=False)
    excel.close()

    # Prepare response object.
    response = HttpResponse(f.getvalue(),
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f'{slugify(analyses[0].function.name)}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Close file and return response.
    f.close()
    return response
