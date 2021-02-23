import os
from typing import Optional, cast

import helpers.dbg as dbg
import vendors_amp.kibot.data.config as vkdcon
import vendors_amp.common.data.types as vkdtyp


class FilePathGenerator:
    FREQ_PATH_MAPPING = {
        vkdtyp.Frequency.Daily: "daily",
        vkdtyp.Frequency.Minutely: "1min",
        vkdtyp.Frequency.Tick: "tick",
    }

    CONTRACT_PATH_MAPPING = {
        vkdtyp.ContractType.Continuous: "continuous_",
        vkdtyp.ContractType.Expiry: "",
    }

    ASSET_TYPE_PREFIX = {
        vkdtyp.AssetClass.ETFs: "all_etfs_",
        vkdtyp.AssetClass.Stocks: "all_stocks_",
        vkdtyp.AssetClass.Forex: "all_forex_pairs_",
        vkdtyp.AssetClass.Futures: "all_futures",
        vkdtyp.AssetClass.SP500: "sp_500_",
    }

    def generate_file_path(
        self,
        symbol: str,
        frequency: vkdtyp.Frequency,
        asset_class: vkdtyp.AssetClass = vkdtyp.AssetClass.Futures,
        contract_type: Optional[vkdtyp.ContractType] = None,
        unadjusted: Optional[bool] = None,
        ext: vkdtyp.Extension = vkdtyp.Extension.Parquet,
    ) -> str:
        """
        Get the path to a specific kibot dataset on s3.

        Parameters as in `read_data`.
        :return: path to the file
        """

        freq_path = self.FREQ_PATH_MAPPING[frequency]

        asset_class_prefix = self.ASSET_TYPE_PREFIX[asset_class]

        modifier = self._generate_modifier(
            asset_class=asset_class,
            contract_type=contract_type,
            unadjusted=unadjusted,
        )

        dir_name = f"{asset_class_prefix}{modifier}{freq_path}"
        file_path = os.path.join(dir_name, symbol)

        if ext == vkdtyp.Extension.Parquet:
            # Parquet files are located in `pq/` subdirectory.
            file_path = os.path.join("pq", file_path)
            file_path += ".pq"
        elif ext == vkdtyp.Extension.CSV:
            file_path += ".csv.gz"

        # TODO(amr): should we allow pointing to a local file here?
        # or rename the method to `generate_s3_path`?
        file_path = os.path.join(vkdcon.S3_PREFIX, file_path)
        return file_path

    def _generate_contract_path_modifier(
        self, contract_type: vkdtyp.ContractType
    ) -> str:
        contract_path = self.CONTRACT_PATH_MAPPING[contract_type]
        return f"_{contract_path}contracts_"

    @staticmethod
    def _generate_unadjusted_modifier(unadjusted: bool) -> str:
        adjusted_modifier = "unadjusted_" if unadjusted else ""
        return adjusted_modifier

    def _generate_modifier(
        self,
        asset_class: vkdtyp.AssetClass,
        unadjusted: Optional[bool] = None,
        contract_type: Optional[vkdtyp.ContractType] = None,
    ) -> str:
        """
        Generate a modifier to the file path, based on some asset class
        options.

        :param asset_class: asset class
        :param unadjusted: required for asset classes of type: `stocks` & `etfs`
        :param contract_type: required for asset class of type: `futures`
        :return: a path modifier
        """
        modifier = ""
        if asset_class == vkdtyp.AssetClass.Futures:
            dbg.dassert_is_not(
                contract_type,
                None,
                msg="`contract_type` is a required arg for asset class: 'futures'",
            )
            modifier = self._generate_contract_path_modifier(
                contract_type=contract_type
            )
        elif asset_class in [
            vkdtyp.AssetClass.Stocks,
            vkdtyp.AssetClass.ETFs,
            vkdtyp.AssetClass.SP500,
        ]:
            dbg.dassert_is_not(
                unadjusted,
                None,
                msg="`unadjusted` is a required arg for asset "
                    "classes: 'stocks' & 'etfs' & 'sp_500'",
            )
            modifier = self._generate_unadjusted_modifier(
                unadjusted=cast(bool, unadjusted)
            )
        return modifier
